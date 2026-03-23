import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        try:
            # Test with trailing slash
            print("Testing /journals/ ...")
            response = await client.get("http://localhost:8000/journals/")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text[:500]}")
            
            # Test without trailing slash
            print("\nTesting /journals ...")
            response = await client.get("http://localhost:8000/journals")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
