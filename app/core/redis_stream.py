import asyncio
import json
import os
from typing import Optional, Callable, List, Any, Dict
from loguru import logger
from redis.asyncio import Redis


class RedisStreamConsumer:
    """
    Base consumer class for reading and processing messages from Redis Streams
    using Consumer Groups.

    Features:
    - Automatically creates Consumer Group if it does not exist.
    - Asynchronous message consumption using asyncio.
    - ACK + delete message after successful processing.
    - Supports reclaiming abandoned / pending messages.
    - Can be extended to implement custom business logic via `handle_record`.

    Attributes:
        redis (Redis):
            Async Redis client.

        stream_name (str):
            Name of the Redis Stream to consume.

        group_name (str):
            Name of the Consumer Group.

        consumer_name (str):
            Name of the current consumer.
            If not provided, it is auto-generated from hostname + pid.

        read_items (int):
            Number of messages to read per batch.

        block_ms (int):
            Blocking time while waiting for new messages (milliseconds).

        check_abandoned_ms (int):
            Minimum time threshold to consider a message as abandoned.

        disable_abandoned_check (bool):
            If True, disables reclaiming abandoned messages.

        exit_loop (bool):
            Flag used to safely stop loops.
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

        # If consumer name is not provided, use hostname_pid as default
        self.consumer_name = consumer_name or f"{os.uname().nodename}_{os.getpid()}"

        self.read_items = read_items
        self.block_ms = block_ms
        self.check_abandoned_ms = check_abandoned_ms
        self.disable_abandoned_check = disable_abandoned_check

        self.exit_loop = False
        self._read_task: Optional[asyncio.Task] = None
        self._abandoned_task: Optional[asyncio.Task] = None

    async def setup(self):
        """Initialize Consumer Group if it does not exist."""
        try:
            await self.redis.xgroup_create(
                self.stream_name, self.group_name, id="$", mkstream=True
            )
            logger.bind(context="Stream").info(
                f"Consumer group {self.group_name} created for {self.stream_name}"
            )
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.bind(context="Stream").debug(
                    f"Consumer group {self.group_name} already exists"
                )
            else:
                logger.bind(context="Stream").error(f"Error creating group: {e}")
                raise

    async def handle_record(self, record: Dict[str, Any]):
        """This method must be overridden by subclasses to implement business logic."""
        raise NotImplementedError("Subclasses must implement handle_record")

    async def ack_ids(self, ids: List[str]):
        """ACK processed messages and delete them from stream to save memory."""
        if not ids:
            return
        await self.redis.xack(self.stream_name, self.group_name, *ids)
        await self.redis.xdel(self.stream_name, *ids)

    def _parse_item(self, item_array: Any, reclaimed: bool = False) -> Dict[str, Any]:
        """Convert Redis Stream message format into a dictionary."""
        message_id, fields = item_array

        ret = {"recordID": message_id, "reclaimed": reclaimed}

        # fields can be dict (if decode_responses=True) or list (if False)
        if isinstance(fields, dict):
            ret.update(fields)
        else:
            # fields format: [key1, value1, key2, value2, ...]
            for i in range(0, len(fields), 2):
                key = fields[i]
                value = fields[i + 1]
                ret[key] = value

        return ret

    async def _read_group_loop(self):
        """Loop for reading new messages from Redis Stream."""
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
                                logger.bind(context="Stream").error(
                                    f"Error handling record {parsed_msg['recordID']}: {e}"
                                )
                                # If error occurs, ACK previous successful ones then stop batch
                                await self.ack_ids(processed_ids)
                                break

                        await self.ack_ids(processed_ids)

                # Prevent event loop blocking
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.bind(context="Stream").error(f"Read group error: {e}")
                await asyncio.sleep(1)

    async def _check_abandoned_loop(self):
        """Loop for reclaiming abandoned messages."""
        while not self.exit_loop:
            try:
                # 1. Find pending messages older than threshold
                pending = await self.redis.xpending_range(
                    self.stream_name, self.group_name, "-", "+", self.read_items
                )

                if pending:
                    # Filter messages that exceed abandoned threshold
                    ids_to_claim = [
                        p["message_id"]
                        for p in pending
                        if p["time_since_delivered"] > self.check_abandoned_ms
                    ]

                    if ids_to_claim:
                        # 2. Claim ownership of abandoned messages
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
                                    logger.bind(context="Stream").error(
                                        f"Error handling reclaimed record: {e}"
                                    )
                                    await self.ack_ids(processed_ids)
                                    break

                            await self.ack_ids(processed_ids)

                await asyncio.sleep(self.check_abandoned_ms / 1000)

            except Exception as e:
                logger.bind(context="Stream").error(f"Check abandoned error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Start the consumer process."""
        logger.bind(context="Stream").info(
            f"Starting consumer {self.consumer_name} for {self.stream_name}"
        )

        await self.setup()

        self._read_task = asyncio.create_task(self._read_group_loop())

        if not self.disable_abandoned_check:
            self._abandoned_task = asyncio.create_task(self._check_abandoned_loop())

    async def stop(self):
        """Stop the consumer process safely."""
        self.exit_loop = True

        if self._read_task:
            await self._read_task

        if self._abandoned_task:
            await self._abandoned_task

        logger.bind(context="Stream").info(
            f"Stopped consumer {self.consumer_name}"
        )