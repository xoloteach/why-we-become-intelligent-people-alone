"""Run a command and record wall time, CPU model, cores, RAM, peak RSS (children) and tool versions to $PERF_DIR/<job>.json.
Usage: perf.py JOB [--workers N] -- cmd args..."""
import os, sys, json, time, subprocess, resource, platform
a = sys.argv[1:]; job = a[0]; i = a.index('--'); opts = a[1:i]; cmd = a[i + 1:]
workers = int(opts[opts.index('--workers') + 1]) if '--workers' in opts else None
t0 = time.time(); rc = subprocess.call(cmd); dt = time.time() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
cpu = next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), platform.processor())
ram = int(next(l.split()[1] for l in open('/proc/meminfo') if l.startswith('MemTotal'))) / 1048576
def ver(c):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=20).stdout.splitlines()[0]
    except Exception: return None
d = os.environ.get('PERF_DIR', 'perf'); os.makedirs(d, exist_ok=True)
json.dump({'job': job, 'cmd': ' '.join(cmd)[:300], 'rc': rc, 'seconds': round(dt, 1), 'cpu': cpu, 'cores': os.cpu_count(), 'ram_gb': round(ram, 1),
           'max_rss_mb': round(ru.ru_maxrss / 1024, 1), 'user_s': round(ru.ru_utime, 1), 'sys_s': round(ru.ru_stime, 1), 'bake_workers': workers,
           'ffmpeg': ver(['ffmpeg', '-version']), 'python': sys.version.split()[0], 'node': ver(['node', '-v']), 'runner': os.environ.get('RUNNER_NAME'),
           'run_id': os.environ.get('GITHUB_RUN_ID')}, open(os.path.join(d, f'{job}.json'), 'w'), indent=1)
print(f'[perf] {job}: rc={rc} {dt:.1f}s maxrss={ru.ru_maxrss / 1024:.0f}MB on {cpu} x{os.cpu_count()}', flush=True); sys.exit(rc)
