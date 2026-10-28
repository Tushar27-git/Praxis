"""One local basic-army diagnostic. Ctrl+C stops future commands."""
from pathlib import Path
import sys
import argparse
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coc_advisor.device import AdbClient,find_adb
from coc_advisor.stream import VideoStream
from coc_advisor.runtime import AttackRuntime


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true',help='Explicitly enable one live Regular Battle (10 gold), never purchases/gems')
    parser.add_argument('--max-inputs',type=int,default=40)
    args=parser.parse_args()
    if not args.execute:
        print('No game inputs enabled. Use the fixture tests for offline replay; --execute requires explicit live-run approval.')
        return
    if not 1<=args.max_inputs<=40:parser.error('Input limit must be between1 and40')
    stop=threading.Event(); client=AdbClient(find_adb()); stream=VideoStream(client,'127.0.0.1:5555')
    try:
        stream.start(); deadline=time.monotonic()+5
        while stream.latest() is None and time.monotonic()<deadline:time.sleep(.05)
        runtime=AttackRuntime(client,stream,stop,lambda text:print(text,flush=True),args.max_inputs)
        print('RESULT',runtime.run(timeout=240),flush=True)
    except KeyboardInterrupt:stop.set()
    finally:stop.set(); stream.stop()


if __name__=='__main__':main()
