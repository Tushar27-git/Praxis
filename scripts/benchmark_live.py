"""Read-only stream benchmark; never sends game input."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coc_advisor.device import AdbClient,find_adb
from coc_advisor.stream import VideoStream


def main():
    p=argparse.ArgumentParser(); p.add_argument('--seconds',type=float,default=60)
    args=p.parse_args(); started=time.monotonic(); stream=VideoStream(AdbClient(find_adb()),'127.0.0.1:5555')
    samples=[]; seen=0; first=None
    try:
        stream.start(); deadline=time.monotonic()+args.seconds
        while time.monotonic()<deadline:
            frame=stream.latest()
            if frame and frame.sequence!=seen:
                now=time.monotonic(); seen=frame.sequence
                if first is None: first=now
                samples.append({'sequence':seen,'pts_us':frame.source_pts_us,
                    'decode_ms':frame.capture_ms,'age_upper_ms':(now-frame.requested_at)*1000 if frame.requested_at else None})
            time.sleep(.005)
        last=stream.latest()
        if not last: raise RuntimeError('No decoded video frames received: '+' '.join(stream.logs))
        dest=Path('output/native'); dest.mkdir(parents=True,exist_ok=True)
        last.image.save(dest/'stream-last.png')
        ages=sorted(x['age_upper_ms'] for x in samples if x['age_upper_ms'] is not None)
        report={'seconds':args.seconds,'frames':stream.count,'fps':stream.count/args.seconds,
            'startup_ms':(first-started)*1000 if first else None,'size':last.image.size,
            'clock_probe_rtt_ms':(stream.clock.host_after-stream.clock.host_before)*1000,
            'source_age_bound': 'causal second-socket startup barrier +1000ppm drift margin; no uptime epoch assumption',
            'age_upper_ms':{f'p{pct}':ages[min(len(ages)-1,int(len(ages)*pct/100))] for pct in (50,95,99)} if ages else None,
            'unknown_age_frames':len(samples)-len(ages),'logs':stream.logs,'samples':samples}
        (dest/'stream-benchmark.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in report.items() if k not in ('samples','logs')},indent=2),flush=True)
    finally:
        t=time.monotonic(); stream.stop(); print('stop_ms',round((time.monotonic()-t)*1000),flush=True)


if __name__=='__main__': main()
