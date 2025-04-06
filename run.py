from typing import Optional
from warnings import catch_warnings
from RPLidarC1 import RPLidar
import asyncio
import logging
import time


async def main(lidar: RPLidar):
    # lidar.healthcheck()
    lidar.start_scan()
    # lidar.get_info()
    print(lidar.coro_list)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(wait_and_stop(5, lidar.stop_event))
        tg.create_task(queue_printer(lidar.output_queue, lidar.stop_event))
        for coro in lidar.coro_list:
            tg.create_task(coro)
    print(lidar.output_dict)
    reset(lidar)


async def wait_and_stop(t, event: asyncio.Event):
    print("Start wait for end event")
    await asyncio.sleep(t)
    print("Setting stop event")
    event.set()


async def queue_printer(q: asyncio.Queue, event: asyncio.Event):
    print("Start queue listener")
    while not event.is_set():
        if q.qsize() < 10:
            print("Printer sleeping for more data")
            await asyncio.sleep(0.1)
        out: dict = await q.get()
        print(out)


def reset(lidar: RPLidar):
    print("Resetting before shutdown.")
    lidar.clear_input_buffer()
    lidar._send_command(lidar.RESET_BYTE)
    lidar.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=0)
    lidar = RPLidar("/dev/ttyUSB0", 460800)

    try:
        asyncio.run(main(lidar))
    except KeyboardInterrupt:
        time.sleep(1)
        reset(lidar)
