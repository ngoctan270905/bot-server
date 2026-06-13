from typing import Optional

from bson import ObjectId

from app.repositories.base_repo import BaseRepository

class CustomerRepository(BaseRepository):
    """
    Repository cho collection 'Customer'.
    """

    async def get_by_cid_and_social_page_id(
            self,
            customer_cid: str,
            social_page_id: ObjectId
    ) -> Optional[dict]:
        """
        Lấy khách hàng theo cid và socialPageId.
        """
        query = {
            "cid": customer_cid,
            "socialPageId": social_page_id
        }

        customer = await self.find_one(
            filter=query
        )

        return customer
