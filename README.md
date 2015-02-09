# bgpchart

Get charts on BGP prefixes and peers for a given AS-number. Data is based on 
Hurricane Electric's BGP toolkit. The charts are all in PNG format.

### Chart types
All charts are provided with data from the last 90-day period. And each chart
can be shown with either IPv4 data or IPv6.

 * **Prefixes announced**: number of prefixes announced by the AS.
 * **Originated prefixes**: number of prefixes owned by the AS.
 * **Peer count**: number of peers observed as neighbors to the given AS.

Here is an example of a chart (`bgpchart -c p AS2828`):

![Chart example](https://raw.githubusercontent.com/toringe/bgpchart/master/example.png)

### Usage

    usage: bgpchart.py [-h] [-ip {v4,v6}] [-c {a,o,p}] [-o path] [-v] asn
    
    positional arguments:
      asn          AS-number to lookup
    
    optional arguments:
      -h, --help   show this help message and exit
      -ip {v4,v6}  IP version 4 (default) or 6 statistics
      -c {a,o,p}   Chart type: prefixes [a]nnounced (default) or [o]riginated,
                   or [p]eer count
      -o path      Output directory where charts are saved
      -v           Verbose console output (debugging)

### Examples

Get default chart (Announced IPv4 Prefixes) for AS2828 (XO Communications).

    bgpchart AS2828

Since we did't specify an output file, the chart is saved in your current 
directory as the file `AS2828-v4-a.png`.

Next, we specify both the IP version, chart type and output file.

    bgpchart -ip v6 -c p -o /home/user/chart.png AS2828

This will fetch the IPv6 Peers chart for AS2828 and save it as `chart.png` in 
the user's home directory
