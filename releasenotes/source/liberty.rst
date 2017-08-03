===================================
 Liberty Series Release Notes
===================================

**Main updates**

* Added datasource driver for Heat
* Designed and began implementation of new distributed architecture
* Added API call to list available actions for manual reactive enforcement
* Refactored all datasource drivers for improved consistency
* Extended grammar to include insert and delete events
* Improved tempest/devstack support for running in gate
* Added version API
* Improved support for python3
* Reduced debug log volume by reducing messages sent on message bus
* Enabled action execution for all datasources
* Eliminated busy-loop in message bus for reduced cpu consumption
* Improved unit test coverage for API
* Added experimental vm-migration policy enforcement engine
