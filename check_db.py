import asyncio
from app.core.database import get_sessionmaker
from app.models import Ticket
from sqlalchemy import select

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(Ticket))
        tickets = result.scalars().all()
        print(f"Total tickets found: {len(tickets)}")
        for t in tickets:
            print(f"- {t.id}: {t.subject} (status: {t.status})")

if __name__ == "__main__":
    asyncio.run(main())
