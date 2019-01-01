# smugmug-to-b2

This is a command-line tool to copy all of the photos from a 
[SmugMug](https://smugmug.com) account to a bucket in 
[Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html). 
This adds a layer of multi-cloud safety to your photos.  If the
Amazan S3 storage backing SmugMug should fail, you'll still have
your photos.

## Installing

This package is not yet in PyPI, but you can install directly from GitHub:

```bash
pip install git+https://github.com/bwbeach/smugmug-to-b2.git
```

## Config File

The program uses a YAML config file in ~/.smugmug-to-b2 to get
information about the source SmugMug account and the destination
B2 account.

The contents of the file should look like this:

```yaml
config:
  smugmug:
    key: <API key>
    secret: <API secret>
    user: <SmugMug user name>
  b2:
    key: <account ID or application key ID>
    secret: <application key>
    bucket: <bucket name>

```

## Authorizing SmugMug

There's one more step to set up OAUTH with Smugmug.  Run this command
to get a URL:

```bash
smugmug-to-b2 authorize
```

Then visit the URL in prints out, and enter your SmugMug username
and password.  Then the page will display a PIN that you give to
the command like this:

```bash
smugmug-to-b2 set-pin <pin>
```

## Backing Up Photos

Once you have authorized SmugMug, copy all of your photos to B2:

```bash
smugmug-to-b2 backup
```

## To-Do List

* Stop using `rauth`.  It was buggy for API access.  Might as well stop using it for the authorize step.