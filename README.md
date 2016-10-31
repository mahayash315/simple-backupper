simple-backupper
===

## What this is
**simple-backupper** is a simple backup utiity written in python, focusing on just copying specific directories on on a machine using **scp** and **rsync**.
 

## Configuration
Edit **`targets.yaml`** to configure the backup targets and their destinations. An example configuration file would be as follows:

**NOTE** comments are not supported in the yaml file, so make sure to eliminate all of the comments, or the backupper may crash with an error.

```yaml
hostA-dir1:
  Host: hostA
  option: "--delete"
  fileset:
    include: [
      "/path/to/dir1"
    ]
  dest: "/dest/path/to/dir1"
  log: "logs/hostA.log"

hostB-wholeBackup:
  host: hostB
  option: "--delete"
  fileset:
    include: [
      "/"
    ]
    exclude: [
      "/proc",
      "/tmp",
      "/.journal",
      "/.fsck"
    ]
  log: "logs/hostB.log"
```

## Run

Run the backupper as follows:

```bash
$ python backup.py
```
