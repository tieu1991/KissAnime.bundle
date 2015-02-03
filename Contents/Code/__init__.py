####################################################################################################

PREFIX = "/video/KissAnime"

NAME = "KissAnime"

ICON_LIST = "icon-list.png"
ART = "art-default.jpg"
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
	ObjectContainer.art = R(ART)

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
				thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png')
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
		list_watched = page_data.xpath("//*[@id='container']/div[1]/div[2]/div[2]/table//tr/td[3]/a[1][@style='display: inline']")
		show_watched = len(list_watched)
		list = page_data.xpath("//table[@class='listing']//tr")
		show_unwatched = len(list) - 2 - show_watched			
		
		if show_unwatched > 0:
			
			oc.add(DirectoryObject(
				key = Callback(Folders, watched = 0, show_watched = show_watched),
				title = "UnWatched Shows",
				thumb = R(ICON_QUEUE),
				)
			)
		
		if show_watched > 0:
			
			oc.add(DirectoryObject(
				key = Callback(Folders, watched = 1, show_watched = show_watched),
				title = "Watched Shows",
				thumb = R(ICON_QUEUE),
				)
			)
		
	return oc
	
#####################################################################################
# List Folders
#####################################################################################
@route(PREFIX + '/folders')
def Folders(watched, show_watched):
    
	oc = ObjectContainer()		

	ad_bookmark = "http://kissanime.com/BookmarkList"
	
	page_data = HTML.ElementFromURL(ad_bookmark)
	list = page_data.xpath("//table[@class='listing']//tr")
	show_tot = len(list)
	if int(watched) > 0:
		list = list[(show_tot-int(show_watched)):]
	else:
		list = list[2:(show_tot-int(show_watched))]
		
	show_count = len(list)
	
	#set a start point and determine how many objects we will need
	offset = 0
	rotation = (show_count - (show_count % 10)) / 10

	#add a directory object for every 10 shows
	while rotation > 0:
		
		start_show  = offset
		end_show = offset + 10
		start_show_title = list[(start_show)].xpath(".//td//a/@href")[0].rsplit("/",1)[1][:4]
		end_show_title = list[(end_show-1)].xpath(".//td//a/@href")[0].rsplit("/",1)[1][:4]
			
			
		oc.add(DirectoryObject(
			key = Callback(ListShows, start_show = start_show, end_show = end_show, watched = watched, show_watched = show_watched),
			title = start_show_title + "... to " + end_show_title + "...",
			thumb = R(ICON_LIST)
			)
		)
			
		offset += 10
		rotation = rotation - 1
		
	if (show_count % 10) != 0:

		start_show = offset
		end_show = (offset + (show_count % 10))
		start_show_title = list[(start_show)].xpath(".//td//a/@href")[0].rsplit("/",1)[1][:4]
		end_show_title = list[(end_show-1)].xpath(".//td//a/@href")[0].rsplit("/",1)[1][:4]
			
		oc.add(DirectoryObject(
			key = Callback(ListShows, start_show = start_show, end_show = end_show, watched = int(watched), show_watched = int(show_watched)),
			title = start_show_title + "... to " + end_show_title + "...",
			thumb = R(ICON_LIST)
			)
		) 
	
	return oc
	
#####################################################################################
# List Shows
#####################################################################################
@route(PREFIX + "/listshows")	
def ListShows(start_show, end_show, watched, show_watched):

	oc = ObjectContainer()

	ad_bookmark = "http://kissanime.com/BookmarkList"
	
	page_data = HTML.ElementFromURL(ad_bookmark)
	
	list = page_data.xpath("//table[@class='listing']//tr")
	show_tot = len(list)
	if int(watched) > 0:
		list = list[(show_tot-int(show_watched)):]
	else:
		list = list[2:(show_tot-int(show_watched))]
	
	list = list[int(start_show):int(end_show)]
	
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
		start_ep_title = eps_list[(start_ep)].split((show_title + " "),1)[1].split(" ")[1]
		end_ep_title = eps_list[(end_ep-1)].split((show_title + " "),1)[1].split(" ")[1]
		
		oc.add(DirectoryObject(
			key = Callback(ListEpisodes, show_title = show_title, show_url = show_url, start_ep = start_ep, end_ep = end_ep),
			title = "Episodes " + start_ep_title + " - " + end_ep_title,
			thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png')
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
		start_ep_title = eps_list[(start_ep)].split((show_title + " "),1)[1].split(" ")[1]
		end_ep_title = eps_list[(end_ep-1)].split((show_title + " "),1)[1].split(" ")[1]
		
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
		ep_title = each.xpath("./text()")[0].split(show_title,1)[1]
		
		if ep_title.find("_") < 1:
			
			if Prefs["quality"] == "Choose":
			
				oc.add(DirectoryObject(
					key = Callback(Episodes, show_title = show_title, ep_title = ep_title, ep_url = ep_url), 
					title = ep_title
					)
				)
				
			elif Prefs["quality"] == "1080p":
			
				page_data = HTML.ElementFromURL(ep_url)
				mirror_list = page_data.xpath("//*[@id='divDownload']//a/@href")
				len_mirror = len(mirror_list)
				
				found = 0
				i = 0
				while found == 0:
				
					if mirror_list[i].find("itag=37") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 1920x1080"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
							
					elif mirror_list[i].find("itag=22") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 1280x720"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
							
					elif mirror_list[i].find("itag=18") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 640x360"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
					
					i = i + 1
					
					if i == len_mirror:
						found = 1
					
			elif Prefs["quality"] == "720p":
			
				page_data = HTML.ElementFromURL(ep_url)
				mirror_list = page_data.xpath("//*[@id='divDownload']//a/@href")
				len_mirror = len(mirror_list)
				
				found = 0
				i = 0
				while found == 0:
						
					if mirror_list[i].find("itag=22") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 1280x720"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
							
					elif mirror_list[i].find("itag=18") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 640x360"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
					
					i = i + 1
					
					if i == len_mirror:
						found = 1
					
			elif Prefs["quality"] == "360p":
			
				page_data = HTML.ElementFromURL(ep_url)
				mirror_list = page_data.xpath("//*[@id='divDownload']//a/@href")
				len_mirror = len(mirror_list)
				
				found = 0
				i = 0
				while found == 0:
				
					if mirror_list[i].find("itag=18") > 0:
						url = ep_url + "??" + mirror_list[i]
						title = ep_title + " - 640x360"
						oc.add(VideoClipObject(
							url = url,
							title = title
							)
						)
						found = 1
					
					i = i + 1
					
					if i == len_mirror:
						found = 1
					
	return oc

#####################################################################################
# Episodes
#####################################################################################

@route(PREFIX + "/episodes")	
def Episodes(show_title, ep_title, ep_url):

	oc = ObjectContainer(title1=show_title)
	
	page_data = HTML.ElementFromURL(ep_url)
	mirror_list = page_data.xpath("//*[@id='divDownload']//a/@href")	
	
	for each in mirror_list:
	
		if each.find("itag=37") > 0:
			url = ep_url + "??" + each
			title = "1920x1080"

			oc.add(VideoClipObject(
				url = url,
				title = title
				)
			)
				
		if each.find("itag=22") > 0:
			url = ep_url + "??" + each
			title = "1280x720"
			
			oc.add(VideoClipObject(
				url = url,
				title = title
				)
			)
				
		if each.find("itag=18") > 0:
			url = ep_url + "??" + each
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
