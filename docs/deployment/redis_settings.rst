==============
Redis settings
==============

Redis configuration (on Debian based systems) is in /etc/redis/redis.conf. Here is a list of configuration options you might want to change. 

Link to offical Redis documentation: http://redis.io/topics/config .

save
----

Example::

    save 900 1
    save 300 10
    save 60 10000

If you don't want Redis to save data to disk comment (or remove) all save options. Default values are too low for high traffic Booktype site.

appendfsync
-----------

Example::

    # appendfsync always
    appendfsync everysec
    # appendfsync no

This option works only if you are saving data to disk. Choose "no" or "everysec" if you have a lot of traffic on the site.
