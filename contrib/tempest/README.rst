The contrib/tempest directory contains the files necessary to integrate
Congress with tempest for functional testing.

NOTE: One needs to have the tempest source codebase to do this. The easiest
way to get tempest setup on your system is to add tempest to
ENABLED_SERVICES in devstack (when one runs ./stack.sh). Then:

To setup with tempest:

    $ cp -r contrib/tempest/tempest/ /opt/stack/tempest/

Then, run tests within tempest as you normally would (via ./run_tempest.sh
or via tox)
