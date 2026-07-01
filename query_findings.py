import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models.finding import Finding
from app.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        stmt = select(Finding).where(Finding.audience_guidance != None)
        result = await session.execute(stmt)
        findings = result.scalars().all()
        print(f"Total findings in DB with guidance: {len(findings)}")
        for f in findings[:10]:
            print(f"- Title: {f.title}")
            print(f"  Type: {f.type}")
            print(f"  Guidance: {f.audience_guidance}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
