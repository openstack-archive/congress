# NOTE(ekcs): monkey_patch upfront to ensure all imports get patched modules
import eventlet
eventlet.monkey_patch()
