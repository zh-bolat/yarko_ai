import asyncio

async def my_coro():
    print("Inside coro")
    await asyncio.sleep(1)
    print("Coro done")
    return "OK"

fn = lambda: my_coro()

async def main():
    print("Calling fn")
    res = await fn()
    print("Result:", res)

asyncio.run(main())
