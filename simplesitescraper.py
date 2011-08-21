#!usr/bin/env python

import re
import urllib2

class SimpleSiteScraper(object):

    def __init__(self, url, recursive=False, page_depth=5):
        # TODO: Document ;)
        
        self.url = url
        self.recursive = recursive
        self.page_depth = page_depth
        self.link_blacklist = None
        
        # By default we just use the domain of the URL we're scraping. In theory
        # you should be able to set to a Python regex string to allow subdomains
        # for example.
        # TODO: Capture cases where self.url is invalid URL. Right now this will
        #       result in an uncaught exception.
        # TODO: Test various regex.
        self.link_regex = re.match('.+?://(.+?)(?:/.*?)?$', self.url).group(1)
        
        # The regular expression that will run on the HTML of every visited link.
        # For demonstration purposes, the default regex will find the 'src'
        # attribute of all 'img' tags.
        self.regex = '<img.+?src=["\'](.+?)["\'].*?\/?>'
        
        # A callable object that will be executed on result of self.regex. It
        # will be passed the current URL and regular expression result. For
        # demonstration purposes, the default will simply return a list.
        self.regex_callback = lambda url, regex_result: [url, regex_result]
        
        # "private" stuff.
        self._link_blacklist_regex = None
        self._current_depth = 0
        self._visited_links = set()

    def get_links(self, html, link_regex=''):
        """
            Return a set of href values from all a elements.
            
            html: The HTML text to search.
            link_regex: An optional regex used to determine whether link should
                be followed.
        """
        # Use a set over a list, because set will strip out duplicates.
        # TODO: Add suppport for relative URLs.
        return set(re.findall('<a.+?href=["\'](http://'+link_regex+'.*?)(?:#.*?)?["\'].+?>',html))

    def _can_visit_link(self, link):
        """
            Return whether or not we 'can' visit supplied link.
            
            Reasons we may not want to visit the link currently include:
                - Link exists in our blacklist.
                - Link exists in our visited links list.
        """
        if self._link_blacklist_regex and re.search(self._link_blacklist_regex, link):
            #print('Ah snap! This ish is blacklisted: %s' % link)
            return False
            
        if link in self._visited_links:
            #print('Damn son! I done already seen this ish: %s' % link)
            return False
        
        return True

    def _scrape_url(self, url):
        """
            Function to [recursively] scrape a URL.
        """
        
        try:
            req = urllib2.Request(url)
            res = urllib2.urlopen(req)
        except urllib2.HTTPError as err:
            # For now silently catch HTTP errors such as 404s
            return
        
        html = res.read()
        
        self.regex_callback(url, re.findall(self.regex, html))
        
        if self.recursive:
            for link in self.get_links(html, self.link_regex):
                if self._can_visit_link(link) and self._current_depth < self.page_depth:
                    self._visited_links.add(link)
                    self._current_depth += 1
                    #print "I'm %d page(s) up in this ish son!" % self._current_depth
                    self._scrape_url(link)
                    self._current_depth -= 1
                if self._current_depth >= self.page_depth:
                    self._current_depth -= 1
                    return

    def scrape(self):
        # Generate link blacklist regular expression.
        if self.link_blacklist:
            self._link_blacklist_regex = re.compile('|'.join(['(%s)' % u for u in s.link_blacklist]))
            
        self._scrape_url(self.url)

if __name__ == '__main__':

    s = SimpleSiteScraper('http://example.com')
    
    # You can optionally supply a list of strings to blacklist. This can be 
    # a single string, full URL, or Python regex string.
    #s.link_blacklist = [
    #    'http://example.com/some_file.html',
    #    'http://example.com/some_dir.*?',
    #    '.+?gallery'
    #]
    
    # Should follow links
    s.recursive = True
        
    # Define a callback for SimpleSiteScraper.regex_callback. We'll just print
    # the img src, number of found img src urls (from our regex) and a comma separated list
    # of the img srcs.
    def print_url_and_zones(url, regex_response):
        print('"%s",%d,"%s"' % (url, len(regex_response), ','.join(regex_response)))
    
    s.regex_callback = print_url_and_zones
    
    # The regex_callback we set prints outupt for a CSV file, so lets set up 
    # a header row for the output before we start our scrape.
    print('"url","num_of_imgs","srcs"')
    
    # Start our scraping!
    s.scrape()
