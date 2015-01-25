####################################################################################################

PREFIX = "/video/KissAnime"

NAME = "KissAnime"

ICON_LIST = "icon-list.png"
ICON_COVER = "icon-cover.png"
ICON_SEARCH = "icon-search.png"
ICON_QUEUE = "icon-queue.png"

BASE_URL = "http://kissanime.com"

RE_txha = Regex("txha = '.*';")

#####################################################################################
# Start
#####################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():

# Setup the default breadcrumb title for the plugin
	ObjectContainer.title1 = NAME

#####################################################################################
# Main Menu
#####################################################################################

# This main function will setup the displayed items.
# Initialize the plugin
@handler(PREFIX, NAME)
def MainMenu():
    	oc = ObjectContainer()
    	oc.add(DirectoryObject(key=Callback(Bookmark), title="Bookmark", thumb = R(ICON_LIST)))
	oc.add(InputDirectoryObject(key=Callback(Search), title = "Search", prompt = "Search for anime?", thumb = R(ICON_SEARCH)))
	return oc

#####################################################################################
# Search
#####################################################################################

@route(PREFIX + "/search")	
def Search(query):
		
	oc = ObjectContainer(title1 = query)
	
	#setup the search request url
	request_url = "http://kissanime.com/Search/Anime"
	referer = "http://kissanime.com/"
	values = {
		'keyword':query
		}

	#do http request for search data
	page = HTTP.Request(request_url, values = values, headers={'referer':referer})
	page_data = HTML.ElementFromString(page)

	list = page_data.xpath("//div[@id='leftside']//table[@class='listing']//tr")
	list = list[2:]
	
	for each in list:

		show_url = BASE_URL + each.xpath(".//td//a/@href")[0]
		page_data = HTML.ElementFromURL(show_url)
		show_title = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]/a/text()")[0]
		show_summary = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]//p")
		i = len(show_summary) - 1
		show_summary = show_summary[i].xpath(".//text()")
		summary = ""
		for each in show_summary:
			summary = summary + " " + each
		show_thumb = page_data.xpath("//div[@id='rightside']//img/@src")[0]
		
		oc.add(DirectoryObject(
			key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
			title = show_title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png')
			)
		)
	
	#check for zero results and display error
	if len(oc) < 1:
		Log ("No shows found! Check search query.")
		return ObjectContainer(header="Error", message="Nothing found! Try something less specific.") 
	
	return oc


#####################################################################################
# Bookmark
#####################################################################################

@route(PREFIX + '/bookmark')
def Bookmark():
    
	oc = ObjectContainer()

	if Prefs["login"] == 0:
		
		for each in Dict:
			show_url = Dict[each]
			page_data = HTML.ElementFromURL(show_url)
			show_title = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]/a/text()")[0]
			show_summary = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]//p")
			i = len(show_summary) - 1
			show_summary = show_summary[i].xpath(".//text()")
			summary = ""
			for each in show_summary:
				summary = summary + " " + each
			show_thumb = page_data.xpath("//div[@id='rightside']//img/@src")[0]
			
			oc.add(DirectoryObject(
				key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
				title = show_title,
				summary = summary,
				thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
				)
			)
		
		#add a way to clear bookmarks list
		oc.add(DirectoryObject(
			key = Callback(ClearBookmarks),
			title = "Clear Bookmarks",
			thumb = R(ICON_QUEUE),
			summary = "CAUTION! This will clear your entire bookmark list!"
			)
		)
		
	else:
		
		#setup the login request url
		request_url = "http://kissanime.com/Login"
		ad_bookmark = "http://kissanime.com/BookmarkList"
		values = {
			'username':Prefs["username"],
			'password':Prefs["password"]
			}

		#do http request for search data
		page = HTTP.Request(request_url, values = values)
		
		page_data = HTML.ElementFromURL(ad_bookmark)
		data = HTML.StringFromElement(page_data)

		list = page_data.xpath("//table[@class='listing']//tr")
		list = list[2:]
		
		for each in list:

			show_url = BASE_URL + each.xpath(".//td//a/@href")[0]
			page_data = HTML.ElementFromURL(show_url)
			show_title = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]/a/text()")[0]
			show_summary = page_data.xpath("//*[@id='leftside']/div[1]/div[2]/div[2]//p")
			i = len(show_summary) - 1
			show_summary = show_summary[i].xpath(".//text()")
			summary = ""
			for each in show_summary:
				summary = summary + " " + each
			show_thumb = page_data.xpath("//div[@id='rightside']//img/@src")[0]
			
			oc.add(DirectoryObject(
				key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
				title = show_title,
				summary = summary,
				thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
				)
			)
		
		#check for zero results and display error
		if len(oc) < 1:
			Log ("No shows found! Check search query.")
			return ObjectContainer(header="Error", message="Nothing found! Try something less specific.") 
	
	return oc

#####################################################################################
# Page Episodes
#####################################################################################
 
@route(PREFIX + "/pageepisodes")
def PageEpisodes(show_title, show_url):

	oc = ObjectContainer(title1 = show_title)
	page_data = HTML.ElementFromURL(show_url)
	show_thumb = page_data.xpath("//div[@id='rightside']//img/@src")[0]
	show_ep_count = len(page_data.xpath("//div[@id='leftside']//table[@class='listing']//tr")) - 2
	eps_list = page_data.xpath("//div[@id='leftside']//table[@class='listing']//tr/td//a/text()")
	eps_list.reverse()
	
	#set a start point and determine how many objects we will need
	offset = 0
	rotation = (show_ep_count - (show_ep_count % 20)) / 20

	#add a directory object for every 20 episodes
	while rotation > 0:
	
		start_ep  = offset
		end_ep = offset + 20
		start_ep_title = eps_list[(start_ep)].replace(" - ","&").rsplit(" ",1)[1]
		end_ep_title = eps_list[(end_ep-1)].replace(" - ","&").rsplit(" ",1)[1]
		
		oc.add(DirectoryObject(
			key = Callback(ListEpisodes, show_title = show_title, show_url = show_url, start_ep = start_ep, end_ep = end_ep),
			title = "Episodes " + start_ep_title + " - " + end_ep_title,
			thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
			)
		)
		
		offset += 20
		rotation = rotation - 1
	
	#if total eps is divisible by 20, add bookmark link and return
	if (show_ep_count % 20) == 0:	
		
		if Prefs["login"] == 0:
			#provide a way to add or remove from favourites list
			oc.add(DirectoryObject(
				key = Callback(AddBookmark, show_title = show_title, show_url = show_url),
				title = "Add Bookmark",
				summary = "You can add " + show_title + " to your Bookmarks list, to make it easier to find later.",
				thumb = R(ICON_QUEUE)
				)
			)	
		
		return oc
	
	#else create directory object for remaining eps
	else:

		start_ep = offset
		end_ep = (offset + (show_ep_count % 20))
		start_ep_title = eps_list[(start_ep)].replace(" - ","&").rsplit(" ",1)[1]
		end_ep_title = eps_list[(end_ep-1)].replace(" - ","&").rsplit(" ",1)[1]
		
		oc.add(DirectoryObject(
			key = Callback(ListEpisodes, show_title = show_title, show_url = show_url, start_ep = start_ep, end_ep = end_ep),
			title = "Episodes " + start_ep_title + " - " + end_ep_title,
			thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
			)
		)

		if Prefs["login"] == 0:
			#provide a way to add or remove from favourites list
			oc.add(DirectoryObject(
				key = Callback(AddBookmark, show_title = show_title, show_url = show_url),
				title = "Add Bookmark",
				summary = "You can add " + show_title + " to your Bookmarks list, to make it easier to find later.",
				thumb = R(ICON_QUEUE)
				)
			)	
		
		return oc

#####################################################################################
# List Episodes
#####################################################################################

@route(PREFIX + "/listepisodes")	
def ListEpisodes(show_title, show_url, start_ep, end_ep):

	oc = ObjectContainer(title1 = show_title)
	page_data = HTML.ElementFromURL(show_url)
	eps_list = page_data.xpath("//div[@id='leftside']//table[@class='listing']//tr/td//a")
	eps_list.reverse()
	
	for each in eps_list[int(start_ep):int(end_ep)]:
		ep_url = BASE_URL + each.xpath("./@href")[0]
		ep_title = each.xpath("./text()")[0].replace(" - ","&").rsplit(" ",2)
		ep_title = ep_title[1] + " " + ep_title[2]
		
		if Prefs["quality"] == "Choose":
		
			oc.add(DirectoryObject(
				key = Callback(Episodes, show_title = show_title, ep_title = ep_title, ep_url = ep_url), 
				title = ep_title
				)
			)
			
		elif Prefs["quality"] == "1080p":
		
			page_data = HTML.ElementFromURL(ep_url)
			data = HTML.StringFromElement(page_data)
			
			txha = RE_txha.search(data).group().split("= '",1)[1]
			fmt_stream = txha.split("=",2)[2].split("&",1)[0]
			fmt_stream = fmt_stream.replace("%252C",",").replace("%2f","/").replace("%3f","?").replace("%3d","=").replace("%26","&").replace("%3a",":").replace("https","http")
			
			
			if fmt_stream.find("itag=37") > 0:
				url = ep_url + "??" + fmt_stream.split("37%7C",1)[1].split("%2C",1)[0]
				title = ep_title + " - 1920x1080"

				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)
					
			elif fmt_stream.find("itag=22") > 0:
				url = ep_url + "??" + fmt_stream.split("22%7C",1)[1].split("%2C",1)[0]
				title = ep_title + " - 1280x720"
				
				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)
					
			elif fmt_stream.find("itag=18") > 0:
				url = ep_url + "??" + fmt_stream.split("18%7C",1)[1]
				title = ep_title + " - 640x360"
					
				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)
				
		elif Prefs["quality"] == "720p":
		
			page_data = HTML.ElementFromURL(ep_url)
			data = HTML.StringFromElement(page_data)
			
			txha = RE_txha.search(data).group().split("= '",1)[1]
			fmt_stream = txha.split("=",2)[2].split("&",1)[0]
			fmt_stream = fmt_stream.replace("%252C",",").replace("%2f","/").replace("%3f","?").replace("%3d","=").replace("%26","&").replace("%3a",":").replace("https","http")
					
			if fmt_stream.find("itag=22") > 0:
				url = ep_url + "??" + fmt_stream.split("22%7C",1)[1].split("%2C",1)[0]
				title = ep_title + " - 1280x720"
				
				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)
					
			elif fmt_stream.find("itag=18") > 0:
				url = ep_url + "??" + fmt_stream.split("18%7C",1)[1]
				title = ep_title + " - 640x360"
					
				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)
				
		elif Prefs["quality"] == "360p":
		
			page_data = HTML.ElementFromURL(ep_url)
			data = HTML.StringFromElement(page_data)
			
			txha = RE_txha.search(data).group().split("= '",1)[1]
			fmt_stream = txha.split("=",2)[2].split("&",1)[0]
			fmt_stream = fmt_stream.replace("%252C",",").replace("%2f","/").replace("%3f","?").replace("%3d","=").replace("%26","&").replace("%3a",":").replace("https","http")
					
			if fmt_stream.find("itag=18") > 0:
				url = ep_url + "??" + fmt_stream.split("18%7C",1)[1]
				title = ep_title + " - 640x360"
					
				oc.add(VideoClipObject(
					url = url,
					title = title
					)
				)		
	return oc

#####################################################################################
# Episodes
#####################################################################################

@route(PREFIX + "/episodes")	
def Episodes(show_title, ep_title, ep_url):

	oc = ObjectContainer(title1=show_title)
	
	page_data = HTML.ElementFromURL(ep_url)
	data = HTML.StringFromElement(page_data)
	
	txha = RE_txha.search(data).group().split("= '",1)[1]
	fmt_stream = txha.split("=",2)[2].split("&",1)[0]
	fmt_stream = fmt_stream.replace("%252C",",").replace("%2f","/").replace("%3f","?").replace("%3d","=").replace("%26","&").replace("%3a",":").replace("https","http")
	
	
	if fmt_stream.find("itag=37") > 0:
		url = ep_url + "??" + fmt_stream.split("37%7C",1)[1].split("%2C",1)[0]
		title = "1920x1080"

		oc.add(VideoClipObject(
			url = url,
			title = title
			)
		)
			
	if fmt_stream.find("itag=22") > 0:
		url = ep_url + "??" + fmt_stream.split("22%7C",1)[1].split("%2C",1)[0]
		title = "1280x720"
		
		oc.add(VideoClipObject(
			url = url,
			title = title
			)
		)
			
	if fmt_stream.find("itag=18") > 0:
		url = ep_url + "??" + fmt_stream.split("18%7C",1)[1]
		title = "640x360"
			
		oc.add(VideoClipObject(
			url = url,
			title = title
			)
		)
	
	
	return oc
	
#####################################################################################
# Add Bookmark
#####################################################################################	
@route(PREFIX + "/addbookmark")
def AddBookmark(show_title, show_url):
	
	Dict[show_title] = show_url
	Dict.Save()
	return ObjectContainer(header=show_title, message='This show has been added to your bookmarks.')
	
#####################################################################################
# Clear Bookmark
#####################################################################################
@route(PREFIX + "/clearbookmarks")
def ClearBookmarks():

	Dict.Reset()
	return ObjectContainer(header="My Bookmarks", message='Your bookmark list has been cleared.')
