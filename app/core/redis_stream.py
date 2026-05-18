import asyncio
import json
import os
from typing import Optional, Callable, List, Any, Dict
from loguru import logger
from redis.asyncio import Redis

class RedisStreamConsumer:
    """
    Consumer base class dùng để đọc và xử lý message từ Redis Stream
    thông qua Consumer Group.

    Features:
    - Tự tạo Consumer Group nếu chưa tồn tại.
    - Consume message bất đồng bộ bằng asyncio.
    - ACK + xóa message sau khi xử lý thành công.
    - Hỗ trợ reclaim (claim lại) message bị abandon / pending quá lâu.
    - Có thể kế thừa để implement business logic riêng qua `handle_record`.

    Attributes:
        redis (Redis):
            Redis async client.

        stream_name (str):
            Tên Redis Stream cần consume.

        group_name (str):
            Tên Consumer Group.

        consumer_name (str):
            Tên consumer hiện tại.
            Nếu không truyền vào sẽ tự sinh từ hostname + pid.

        read_items (int):
            Số lượng message đọc mỗi lần.

        block_ms (int):
            Thời gian block khi chờ message mới (milliseconds).

        check_abandoned_ms (int):
            Thời gian tối thiểu để xem một message là abandoned.

        disable_abandoned_check (bool):
            Nếu True thì tắt reclaim abandoned message.

        exit_loop (bool):
            Flag dùng để stop loop an toàn.

    Usage:
        Kế thừa class này và override `handle_record`.

    """
    def __init__(
        self,
        redis_client: Redis,
        stream_name: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        read_items: int = 5,
        block_ms: int = 1000,
        check_abandoned_ms: int = 2000,
        disable_abandoned_check: bool = False
    ):
        self.redis = redis_client
        self.stream_name = stream_name
        self.group_name = group_name
        # Nếu không có tên consumer, lấy hostname_pid làm mặc định
        self.consumer_name = consumer_name or f"{os.uname().nodename}_{os.getpid()}"

        self.read_items = read_items
        self.block_ms = block_ms
        self.check_abandoned_ms = check_abandoned_ms
        self.disable_abandoned_check = disable_abandoned_check

        self.exit_loop = False
        self._read_task: Optional[asyncio.Task] = None
        self._abandoned_task: Optional[asyncio.Task] = None

    async def setup(self):
        """Khởi tạo Consumer Group nếu chưa tồn tại."""
        try:
            await self.redis.xgroup_create(
                self.stream_name, self.group_name, id="$", mkstream=True
            )
            logger.bind(context="Stream").info(f"Consumer group {self.group_name} created for {self.stream_name}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.bind(context="Stream").debug(f"Consumer group {self.group_name} already exists")
            else:
                logger.bind(context="Stream").error(f"Error creating group: {e}")
                raise

    async def handle_record(self, record: Dict[str, Any]):
        """Hàm này sẽ được override bởi các class con để xử lý business logic."""
        raise NotImplementedError("Subclasses must implement handle_record")

    async def ack_ids(self, ids: List[str]):
        """Xác nhận đã xử lý (ACK) và xóa tin nhắn khỏi stream để tiết kiệm bộ nhớ."""
        if not ids:
            return
        await self.redis.xack(self.stream_name, self.group_name, *ids)
        await self.redis.xdel(self.stream_name, *ids)

    def _parse_item(self, item_array: Any, reclaimed: bool = False) -> Dict[str, Any]:
        """Convert format của Redis Stream sang Dict."""
        message_id, fields = item_array
        # fields là list [key1, value1, key2, value2...]
        ret = {"recordID": message_id, "reclaimed": reclaimed}
        for i in range(0, len(fields), 2):
            key = fields[i]
            value = fields[i+1]
            ret[key] = value
        return ret

    async def _read_group_loop(self):
        """Vòng lặp đọc tin nhắn mới."""
        while not self.exit_loop:
            try:
                # XREADGROUP GROUP {group} {consumer} COUNT {n} BLOCK {ms} STREAMS {stream} >
                streams = await self.redis.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=self.read_items,
                    block=self.block_ms
                )

                if streams:
                    for stream_name, messages in streams:
                        processed_ids = []
                        for msg in messages:
                            parsed_msg = self._parse_item(msg)
                            try:
                                await self.handle_record(parsed_msg)
                                processed_ids.append(parsed_msg["recordID"])
                            except Exception as e:
                                logger.bind(context="Stream").error(f"Error handling record {parsed_msg['recordID']}: {e}")
                                # Nếu lỗi, vẫn ACK những cái trước đó rồi dừng batch này
                                await self.ack_ids(processed_ids)
                                break

                        await self.ack_ids(processed_ids)

                # Tránh làm nghẽn event loop
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.bind(context="Stream").error(f"Read group error: {e}")
                await asyncio.sleep(1)

    async def _check_abandoned_loop(self):
        """Vòng lặp thu hồi tin nhắn bị treo (Claim abandoned messages)."""
        while not self.exit_loop:
            try:
                # 1. Tìm tin nhắn bị treo lâu hơn check_abandoned_ms
                # XPENDING {stream} {group} - + {count}
                pending = await self.redis.xpending_range(
                    self.stream_name, self.group_name, "-", "+", self.read_items
                )

                if pending:
                    # Lọc ra những cái quá hạn
                    ids_to_claim = [
                        p["message_id"] for p in pending
                        if p["idle"] > self.check_abandoned_ms
                    ]

                    if ids_to_claim:
                        # 2. Claim quyền sở hữu
                        # XCLAIM {stream} {group} {consumer} {min_idle} {ids...}
                        claimed = await self.redis.xclaim(
                            self.stream_name,
                            self.group_name,
                            self.consumer_name,
                            min_idle_time=self.check_abandoned_ms,
                            message_ids=ids_to_claim
                        )

                        if claimed:
                            processed_ids = []
                            for msg in claimed:
                                parsed_msg = self._parse_item(msg, reclaimed=True)
                                try:
                                    await self.handle_record(parsed_msg)
                                    processed_ids.append(parsed_msg["recordID"])
                                except Exception as e:
                                    logger.bind(context="Stream").error(f"Error handling reclaimed record: {e}")
                                    await self.ack_ids(processed_ids)
                                    break
                            await self.ack_ids(processed_ids)

                await asyncio.sleep(self.check_abandoned_ms / 1000)

            except Exception as e:
                logger.bind(context="Stream").error(f"Check abandoned error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Bắt đầu tiến trình consume."""
        logger.bind(context="Stream").info(f"Starting consumer {self.consumer_name} for {self.stream_name}")
        await self.setup()

        self._read_task = asyncio.create_task(self._read_group_loop())
        if not self.disable_abandoned_check:
            self._abandoned_task = asyncio.create_task(self._check_abandoned_loop())

    async def stop(self):
        """Dừng tiến trình consume an toàn."""
        self.exit_loop = True
        if self._read_task:
            await self._read_task
        if self._abandoned_task:
            await self._abandoned_task
        logger.bind(context="Stream").info(f"Stopped consumer {self.consumer_name}")
