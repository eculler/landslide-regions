streamflow_fn = '../data/raw/usgs/streamflow20190717.txt'

site_file = None
with open(streamflow_fn) as streamflow_file:
    for line in streamflow_file:
        if line.startswith('# Data provided for site'):
            site_no = line.split(' ')[-1][:-1]
            if site_file:
                site_file.close()
            site_file = open(
                '../data/processed/usgs/{}.tsv'.format(site_no), 'a')
        if line.startswith('#'):
            continue
        if site_file:
            site_file.write(line)

site_file.close()
