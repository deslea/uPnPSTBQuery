# uPnPSTBQuery
Python application that gets all available recordings on a Fetch set top box and converts to a BAT script, to encode the available recordings to MP4 with VLC. Before running the script, the user can manually edit if desired - eg, to delete commands for recordings that are already saved or otherwise not wanted, break the job into batches, etc.

This is my first public application and I don't know how widely it will transfer to other uPNP or Fetch use cases beyond mine. My Fetch boxes is one distributed for the Australian market; it is not known how universal the config and XML schema for these might be.

The code is heavily commented to assist in adaptation to differently-configured Fetch boxes and/or similar uPNP devices. It is likely that anyone seeking to communicate with a uPNP device will find some aspects of this useful, but it was written originally for my own environment and is offered strictly as-is.
