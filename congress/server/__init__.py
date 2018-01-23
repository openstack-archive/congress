# NOTE(ekcs): monkey_patch upfront to ensure all imports get patched modules
import eventlet
# NOTE(ekcs): get_hub() before monkey_patch() to workaround issue with
# import cycles in eventlet < 0.22.0;
# Based on the worked-around in eventlet with patch
# https://github.com/eventlet/eventlet/commit/b756447bab51046dfc6f1e0e299cc997ab343701
# For details please check https://bugs.launchpad.net/congress/+bug/1746136
eventlet.hubs.get_hub()
eventlet.monkey_patch()
