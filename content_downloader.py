import requests
import pathlib
import string
import time

from socket import gaierror
from urllib3.exceptions import MaxRetryError

from pytube import YouTube	# https://github.com/nficano/pytube | pip install pytube
import praw					# https://github.com/praw-dev/praw  | pip install praw
import prawcore.exceptions


# OS Dependent
# May throw error if filename is too long or contains invalid characters
max_filename_length = 180
valid_filename_chars = '-_.() []{}{}'.format(string.ascii_letters, string.digits) # https://gist.github.com/seanh/93666

# File extension recognized by the bot
pic_filetypes = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.bpg') # Some these filetypes have not been tested
gif_filetypes = ('.gif', '.gifv')

# PRAW Bot Setup
reddit = praw.Reddit('Config', user_agent = 'win:NkdbO36Gn7udFA:v.5 by /u/runtime_exceptions')


# Main Program
def main():
	print('Reddit Content Downloader')
	print('Hint: you can combine subreddits like r/gifs+funny\n')
	# Get subreddit(s)
	input_subreddit = input('Subreddit: r/')
	subreddit = reddit.subreddit(input_subreddit)

	# Checks what type of content the user wants to download
	download_pics = getContentInput('  Download pictures? (y/n): ')
	download_gifs = getContentInput('  Download gifs? (y/n): ')
	download_vids = getContentInput('  Download videos? (y/n): ')
		
	# Checks that a valid number of posts to download has been submitted
	while True:
		try:
			num_posts = int(input('\n# of top daily posts to download: '))
			if num_posts <= 0:
				print('  At least 1 post needs to be downloaded')
				continue
		except ValueError:
			print('  A positive integer (1, 2, etc.) was not given')
			continue
		break
	
	# Start downloading content
	print('\nDownloading content...')
	i = 0
	try:
		for submission in subreddit.top('day', limit=num_posts*3): # Requests extra incase some links are skipped
			if not submission.is_self and i < num_posts:
				url = submission.url
				#print(url)			
				
				if 'gfycat.com' in url and pathlib.Path(url).suffix == '': # Get a downloadable .gif from gfycat link
					url = url.replace('gfycat', 'giant.gfycat') + '.gif'
				
				# Download picture
				if download_pics and any(t in url for t in pic_filetypes):
					i += 1
					download(submission, url, 'pic', num_posts, i)
				
				# Download gif
				elif download_gifs and any(t in url for t in gif_filetypes):
					i += 1
					download(submission, url, 'gif', num_posts, i)
				
				else:
					# Download (youtube) videos
					try:
						if download_vids and 'youtube' in submission.media['type']:
							i += 1
							print(formatDownloadProgress('Downloading ', formatFileName('['+submission.subreddit.display_name+' vid] ' + submission.title, pathlib.Path(url).suffix), i/num_posts))
							try: # Handle attribution links
								if submission.media['oembed']['url']:
									YouTube(submission.media['oembed']['url']).streams.first().download()
							
							except KeyError:
								YouTube(url).streams.first().download()
					except (KeyError, TypeError): # v.redd.it link or other unknown media
						pass

		# Finished downloading, check if results were empty
		if i > 0:
			if i < num_posts:
				print('\nFinished! {}/{} links were unknown and could not be downloaded.'.format(num_posts-i, num_posts))
			else:
				print('\nFinished! All links were downloaded successfully.')
				
			print('Closing in 5 seconds...')
			time.sleep(5)
			
		else:
			selected_content_types = []
			download_pics and selected_content_types.append('pictures')
			download_gifs and selected_content_types.append('gifs')
			download_vids and selected_content_types.append('videos')
			print('Sorry, no {} were found in r/'.format(str(selected_content_types))+subreddit.display_name)
			print('\nClosing in 5 seconds...')
			time.sleep(5)
	
	except prawcore.exceptions.BadRequest:
		print('\nInvalid subreddit(s), please try again. Closing in 5 seconds...')
		time.sleep(5)
		
	except Exception as e:
		print(e.args)
		print(e)
		print('\nError downloading content')
		print('Closing in 15 seconds...')
		time.sleep(15)
	

def download(submission, url, tag, num_posts, i):
	response = requests.get(url)
	if response.ok:
		filename = formatFileName('['+submission.subreddit.display_name+' '+tag+'] ' + submission.title, pathlib.Path(url).suffix)
		try:
			with open(filename, 'wb') as file:
				file.write(response.content)
			print(formatDownloadProgress('Downloaded ', filename, i/num_posts))
			
		except IOError as io_error:
			if io_error.errno == 2:
				print('Invalid filename from ' + submission.permalink)
			else:
				print('IOError from '+submission.permalink+':\n'+'\n'.join([io_error.errno, io_error, io_error.args]))
				time.sleep(1)
			print('Skipping ' + url + '\n')
				
		except Exception as e:
			print(e+'\n'+e.args)
			print('Unknown exception from ' + submission.permalink)
			print('Skipping ' + url)
	else:
		print('No response from '+url+', skipping...\n')
	
	
def formatDownloadProgress(state, filename, percent):
	return str(round(percent*100, 1)) + '% | '+state+' ' + ((filename[:80]+'...') if len(filename)>80 else filename)


def formatFileName(title, filetype_ending):
	valid_filename = ''.join(c for c in title if c in valid_filename_chars)
	
	if len(valid_filename) + len(filetype_ending) <= max_filename_length:
		return valid_filename + filetype_ending
	else:
		return valid_filename[:max_filename_length-3 - len(filetype_ending)] + '...' + filetype_ending  # Limits filename length


def getContentInput(prompt):
	while True:
		user_input = input(prompt).lower()
		if 'y' in user_input:
			return True
		elif 'n' in user_input:
			return False
		else:
			print('Invalid input. Please type y or n')
			continue
		break
		

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('Interrupted')
		time.sleep(2)
