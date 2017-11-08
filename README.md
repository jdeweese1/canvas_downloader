# Canvas Downloader

A simple script that downloads and organizes all posted files from Canvas (University of Michigan's class organization hub). Each time it is run, it downloads only the files that have changed from the last run. 


## Usage
Requires a yaml-formatted config file.

Config file should be formatted like the following:
```yaml
url: https://umich.instructure.com/
term: WN 2017
oauth_token: <personal oauth token>
directory: <directory to download to>
```

The oauth token can be generated from your account under `Settings`

To specify the config file, use the `--config` flag

I have an alias set up as the following:
`alias canvas="python3 $HOME/projects/canvas_downloader/main.py --config $HOME/projects/canvas_downloader/config.yaml"`
