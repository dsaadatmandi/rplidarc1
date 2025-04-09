from rplidarc1 import RPLidar
import asyncio
import logging
import time

"""
This module provides an example of how to use the RPLidar class to perform
a simple scan and process the results.
"""


async def main(lidar: RPLidar):
    """
    Main coroutine that demonstrates how to use the RPLidar class.

    This function creates three tasks:
    1. A task to wait for a specified time and then stop the scan
    2. A task to print the scan results as they are received
    3. A task to perform the scan itself

    After the scan is complete, it prints the final scan results and resets the device.

    Args:
        lidar (RPLidar): An initialized RPLidar instance.
    """
    async with asyncio.TaskGroup() as tg:
        tg.create_task(wait_and_stop(5, lidar.stop_event))
        tg.create_task(queue_printer(lidar.output_queue, lidar.stop_event))
        tg.create_task(lidar.simple_scan(make_return_dict=True))

    print(lidar.output_dict)
    lidar.reset()


async def wait_and_stop(t, event: asyncio.Event):
    """
    Wait for a specified time and then set an event to stop the scan.

    Args:
        t (float): The time to wait in seconds.
        event (asyncio.Event): The event to set when the time has elapsed.
    """
    print("Start wait for end event")
    await asyncio.sleep(t)
    print("Setting stop event")
    event.set()


async def queue_printer(q: asyncio.Queue, event: asyncio.Event):
    """
    Print scan results from a queue until a stop event is set.

    This coroutine continuously reads scan results from the queue and prints them.
    If the queue has fewer than 10 items, it sleeps briefly to allow more data
    to accumulate.

    Args:
        q (asyncio.Queue): The queue containing scan results.
        event (asyncio.Event): An event that signals when to stop printing.
    """
    print("Start queue listener")
    while not event.is_set():
        if q.qsize() < 10:
            print("Printer sleeping for more data")
            await asyncio.sleep(0.1)
        out: dict = await q.get()
        print(out)


if __name__ == "__main__":
    logging.basicConfig(level=0)
    lidar = RPLidar("/dev/ttyUSB0", 460800)

    try:
        asyncio.run(main(lidar))
    except KeyboardInterrupt:
        time.sleep(1)
        lidar.reset()
