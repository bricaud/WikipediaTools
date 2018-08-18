
import os
import pandas
import codecs
import re
from tqdm import tqdm
import pandas as pd
import time
import gzip

pagelinksR = re.compile("\((\d+),"      # pl_from             (source page id)
						 + "(\d+),"        # page_namespace      (namespace number)
						 + "'(.*?)',"      # page_title          (page title w/o namespace)
						 + "(\d+)\)"       # pl_from_ns          (source page namespace)
)

redirectR = re.compile("\((\d+),"      # rd_from (page ID number)
						 + "(\d+),"        # rd_namespace
						 + "'(.*?)',"      # rd_title
						 + "(.*?),"        # rd_interwiki
						 + "(.*?)\)"       # rd_fragment
		)

pageidR = re.compile("\((\d+),"      # page_id             (page ID number)
						 + "(\d+),"        # page_namespace      (namespace number)
						 + "'(.*?)',"      # page_title          (page title w/o namespace)
						 + "'(.*?)',"      # page_restrictions   (protected pages have 'sysop' here)
						 + "(\d+),"        # page_counter        (view counter, disabled on WP)
						 + "([01]),"       # page_is_redirect
						 + "([01]),"       # page_is_new
						 + "([\d\.]+?),"   # page_random         (for random page function)
						 + "'(\d{14})',"   # page_touched        (cache update timestamp)
						 + "(.*?),"        # page_links updated (timestamp or null)
						 + "(\d+),"        # page_latest      (namespace number)
						 + "(\d+),"        # page_len      (namespace number)
						 + "(.*?)\)"       # page_content_model          (page content model)
		)

def reduce2ns_pagelinks(data_list,namespace):
	namespace = str(namespace)
	return [(info[0],info[2]) for info in data_list if (info[1] == namespace and info[3] == namespace)]
def reduce2ns_redirect(data_list,namespace):
	namespace = str(namespace)
	return [(info[0],info[2]) for info in data_list if (info[1] == namespace)]
def reduce2ns_page(data_list,namespace):
	namespace = str(namespace)
	return [(info[0],info[2]) for info in data_list if (info[1] == namespace)]

def file2df(file,regexparser,reduce2ns,ns):
	print('Extracting data from ',file)
	start = time.time()
	wrapper = codecs.getreader('utf-8')
	with gzip.open(file, 'rb') as f:
		wf = wrapper(f,errors='replace')
		#wf = f
		count = 0
		pageid_list = []
		for line in tqdm(wf):
			count += 1
			info_list = regexparser.findall(line)
			#print('Length',len(info_list))
			valid_pages = reduce2ns(info_list,ns)
			if valid_pages:
				pageid_list += valid_pages
			#if (count % 100) == 0:
			#	print(count)
	duration = time.time() - start
	print('time: {} min {} s.'.format(int(duration/60),int(duration%60)))
	print('Lines processed', count)
	return pageid_list





if __name__ == "__main__":

	input_file = '/home/benjamin/wikipedia/Wikipedia/enwiki-20180801-pagelinks.sql.gz'
#	input_file = '/home/benjamin/wikipedia/Wikipedia/enwiki-20180801-redirect.sql.gz'
#	input_file = '/home/benjamin/wikipedia/Wikipedia/enwiki-20180801-page.sql.gz'
	folder,filename = os.path.split(input_file)


	if 'pagelinks' in filename:
		print('Extracting links')
		regex_string = pagelinksR
		data_filter = reduce2ns_pagelinks
		outname = 'pagelinks'
	elif 'page' in filename:
		print('Extracting pages ids and titles')
		regex_string = pageidR
		data_filter = reduce2ns_page
		outname = 'pageid'
	elif 'redirect' in filename:
		print('Extracting redirects')
		regex_string = redirectR
		data_filter = reduce2ns_redirect
		outname = 'redirect'
	else:
		print('Wrong type of file.')
		raise ValueError('Can not process this type of file.')

	p_list = file2df(input_file,regex_string,data_filter,'0')

	df=pandas.DataFrame(p_list,columns=['sourceId','TargetTitle'])
	df.sourceId = df.sourceId.astype(int)
	print('Nb of entries:',len(df))
	outfile = os.path.join(folder,outname + '.gz')
	print('Saving dataframe to ',outfile)
	start = time.time()
	df.to_pickle(outfile)
	duration = time.time() - start
	print('time to compress and save: {} min {} s.'.format(int(duration/60),int(duration%60)))