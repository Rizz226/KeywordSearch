import os
import requests
import smtplib
import time

from email.mime.text import MIMEText

alert_email_account	= 'EMAILADDRESS'					
alert_email_pass	= 'EMAIL PASSWORD'								
searx_url 			= "http://127.0.0.1:8080/?"
max_sleep_time 		= 120

# read keywords list
with open("keywords.txt", "r") as fd:
	file_contents 	= fd.read()
	keywords		= file_contents.splitlines()

if not os.path.exists("keywords"):
	os.mkdir("keywords")

#
# send email
#
def send_alert(alert_email):

	email_body = "The following keyword hits were just found:\r\n\r\n"

	# searx results walk-through
	if alert_email.has_key("searx"):
		for keyword in alert_email['searx']:
			email_body += "\r\nKeyword: %s\r\n\r\n" % keyword
			for keyword_hit in alert_email['searx'][keyword]:
				email_body += "%s\r\n" % keyword_hit

	# Pastebin results
	# if alert_email.has_key("pastebin"):
	#
	#	for paste_id in alert_email['pastebin']:
	#
	#		email_body += "\r\nPastebin Link: https://pastebin.com/%s\r\n" % paste_id
	#		email_body += "Keywords:%s\r\n" % ",".join(alert_email['pastebin'][paste_id][0])
	#		email_body += "Paste Body:\r\n%s\r\n\r\n" % alert_email['pastebin'][paste_id][1]


	# build the email message
	msg = MIMEText(email_body)
	msg['Subject']	= "OSINT Keyword Alert"
	msg['From'] 	= alert_email_account
	msg['To'] 		= alert_email_account

	server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
	server.ehlo()
	server.login(alert_email_account,alert_email_pass)
	server.sendmail(alert_email_account, alert_email_account, msg.as_string())
	server.close()

	print("[!] Alert email sent!")

	return

#
# Verify that the URL is new
#
def check_urls(keyword,urls):
	new_urls = []
	if os.path.exists("keywords/%s.txt" % keyword):
		with open("keywords/%s.txt" % keyword, "r") as fd:	
			stored_urls = fd.read().splitlines()
		for url in urls:
			if url not in stored_urls:
				print("[*] New URL for {0} discovered: {1}".format(keyword,url))
				new_urls.append(url)
	else:
		new_urls = urls

	# store new URL back in the file
	with open("keywords/%s.txt" % keyword,"ab") as fd:
		for url in new_urls:
			fd.write("%s\r\n" % url)
	return new_urls

#
# poll searx instance for keyword
#

def check_searx(keyword):
	hits = []
	# build param dictionary
	params					= {}
	params['q']				= keyword
	params['categories']	= 'general'
	params['time_ranges']	= 'day' # can be day, month, or year
	params['format']		= 'json'
	print ("[*] Querying searx for: {0}".format(keyword))			
	# send the request to searx
	try:
		response = requests.get(searx_url, params=params)
		results = response.json()
	except:
		return hits
	# if results are found, check against stored URL
	if len(results['results']):
		urls = []
		for result in results['results']:
			if result['url'] not in urls:
				urls.append(result['url'])
		hits = check_urls(keyword,urls)
	return hits
#
# Pastebin checking
#
#def check_pastebin(keywords):

	new_ids		= []
	paste_hits	= {}

	# poll Pastebin API
	try:
		response = requests.get("http://pastebin.com/api_scraping.php?limit=500")
	except:
		return paste_hits

	# parse JSON
	result 	= response.json()

	#load stored paste ID's & only check new ones
	if os.path.exists("pastebin_ids.txt"):
		with open("pastbin_ids.txt", "rb") as fd:
			pastebin_ids = fd.read().splitlines()
	else:
		pastebin_ids = []

	for paste in result:

		if paste['key'] not in pastebin_ids:

			new_ids.append(paste['key'])

			# this is a new paste so send another request to retrieve
			# also check for other keywords
			paste_response			= requests.get(paste['scrape_url'])
			paste_body_lower		= paste_response.content.lower()

			keyword_hits = []

			for keyword in keywords:

				if keyword.lower() in paste_body_lower:
					keyword_hits.append(keyword)

			if len(keyword_hits):
				paste_hits[paste['key']] = (keyword_hits,paste_response.content)

				print("[*] Hit on Pastebin for {0}: {1}".format(str(keyword_hits), paste['full_url']))  
	# store new ID's
	with open("pastebin_ids.txt", "ab") as fd:

		for pastebin_id in new_ids:

			fd.write("%s\r\n" % pastebin_id)

	print("[*] Successfully processed %d Pastebin posts." % len(new_ids)) 

	return paste_hits

#
# wrapper to call functions and stuff.
#

def check_keywords(keywords):

	alert_email 		= {}
	time_start = time.time()

	# use the keywords to check searx
	for keyword in keywords:

		#query searx for keyword
		result = check_searx(keyword)

		if len(result):

			if not alert_email.has_key("searx"):
				alert_email['searx'] = {}

			alert_email['searx'][keyword] = result

	# now check for new pastes
	# result = check_pastebin(keywords)

	# if len(result.keys()):

		# we have results, include in email
		alert_email['pastebin'] = result

	time_end	= time.time()
	total_time	= time_end - time_start

	# if the above is completed within the max_sleep_time setting
	# go to sleep. this is for pastebin limiting
	if total_time < max_sleep_time:

		sleep_time = max_sleep_time - total_time

		print("[*] Sleeping for %d s" % sleep_time)				

		time.sleep(sleep_time)
	
	return alert_email

# first search to pop results
check_keywords(keywords)

# now we loooooooooop
while True:

	alert_email = check_keywords(keywords)

	if len(alert_email.keys()):

		# alerts: sendit
		send_alert(alert_email)

