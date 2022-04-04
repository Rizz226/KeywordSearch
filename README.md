
> Python script for long-term monitoring of keywords

# Keyword Monitoring tool v1.0

This is an script to automate searx and (experimentally) pastebin searches, then send them to an email
of your choosing.

This tool requires a text file called "keywords.txt" where you will input your search querys.
if there is no keywords.txt, please create one and seperate each keyword by a line break. A full history
can be found in the /keywords/ directory, it will have URL's seperated by keyword.

This was developed and tested using searx in a Docker container, the commands to start the container are:

``` 
docker pull searx/searx
docker run --rm -d -v ${PWD}/searx:/etc/searx -p 8080:8080 -e BASE_URL=http://localhost:8080/ searx/searx
```

Visit http://localhost:8080 to ensure the container is running properly

Known issue: this script sends an email every time the loop completes. This generates a lot of noise.

Workaround: Send the mail to a dummy email address with forwarding rules to forward any message 
with "HTTP://" or "HTTPS://" in the message body.
