var storyInterval;
$(function() {

	//Table Sorter
	if ($("table.tablesorter").length > 0 ) {
		$("table.tablesorter").tablesorter(); 
	}

	$('div.mainNav > ul.sf-menu').after($('<ul class="secondary-menu sf-menu" />'));
	
	$(".sf-menu").superfish({
        animation: { height: 'show' },
        speed: 300,
        autoArrows: true,
        dropShadows: false
    });
    
	/* NAVIGATION */
    /* This line will control the number of nav items the top nav bar will have */
    $('div.mainNav > ul.secondary-menu').append($('div.mainNav > ul.sf-menu > li:gt(6)'));
	//$('div.mainNav > ul.secondary-menu').append($('div.mainNav > ul.sf-menu > li:gt(5)'));
	//$('div.mainNav > ul.sf-menu > li:gt(5)').remove();
	$('div.mainNav').css({ 'height' : '56px' , 'overflow' : 'visible' });
	$('#header div.mainNav > ul:first.sf-menu > li:last').addClass('lastnavitemli');
	$('#header div.mainNav > ul.sf-menu > li:last a').css({ 'border-right' : 'none' });
	//$('#header div.mainNav ul.secondary-menu li:first').css({ 'background' : 'transparent' });
	/* END NAVIGATION */
	
	/* HOMEPAGE ROTATOR */
	if ($('div#stories').length > 0 ) {
		storyInterval = setInterval("$('div#stories ul#homepage_rotator > li:eq(5) > div > h3 > a').changeStory()", 10000);
		$('div#stories ul#homepage_rotator > li').each(function() {
			$(this).wrapInner('<div class="activator" />');
		});
		
		$('div#stories ul#homepage_rotator').before($('<div id="homepage_rotator_prev">Previous</div>'));
		$('div#stories ul#homepage_rotator').after($('<div id="homepage_rotator_next">Next</div>'));
		$('div#stories div#story_area').append('<div id="story_info" />');
		$('div#stories ul#homepage_rotator').append($('div#stories ul#homepage_rotator > li:lt(2)'));
		
		$('div#stories ul#homepage_rotator > li > div > h3').paintRotator();
		
		$('div#stories ul#homepage_rotator > li:eq(4)').addClass('active');
		$('div#stories ul#homepage_rotator > li > div > h3 > a').padRotator();
		$('div#stories div#homepage_rotator_prev').click(function() {
			$('div#stories ul#homepage_rotator > li:eq(3) > div > h3 > a').click();
			storyInterval = clearInterval(storyInterval);
		});
		
		$('div#stories div#homepage_rotator_next').click(function() {
			$('div#stories ul#homepage_rotator > li:eq(5) > div > h3 > a').click();
			storyInterval = clearInterval(storyInterval);
		});
		
		$('div#stories ul#homepage_rotator > li > div > h3 > a').click(function(event) {
			event.preventDefault();
			$(this).changeStory();
			storyInterval = clearInterval(storyInterval);
		});
	
		$('div#stories ul#homepage_rotator > li:eq(4) > div > h3 > a').changeStory();
	}

	
	/* END HOMEPAGE ROTATOR */
	
	
	/* General Rotator */
	$('.interiorRotate').each(function(){ 
	
		var timeData = $(this).attr('data-time');
		
		if (! timeData) {
			timeData = 4000;
		} else {
			timeData = timeData * 1000;
		}
		
		$(this).after('<div class="intnav"></div><div class="intControls"><div class="prev"><</div><div class="pause">Pause</div><div class="next">></div></div>');
		
		$(this).cycle({ 
			timeout: timeData,
			fx:     'fade', 
			speed:  'fast', 
			pause:  $(this).next().next('.intControls').children('.pause'), 
			prev:   $(this).next().next('.intControls').children('.prev'), 
			next:  $(this).next().next('.intControls').children('.next'), 
			pager:  $(this).next('.intnav')
		}).hover(
			function(){
				$(this).next().next('.intControls').children('.pause').text('Play');
				$(this).cycle('pause'); 
			},
			function(){
				$(this).next().next('.intControls').children('.pause').text('Pause');
				$(this).cycle('resume'); 
		});
		
		$(this).next().next('.intControls').children('.pause').click(function(){
			if($(this).text() == "Pause"){
				$(this).text('Play');
				$(this).parent().prev().prev().cycle('pause');
			} else {
				$(this).text('Pause');
				$(this).parent().prev().prev().cycle('resume');
			}
		});
	});
	
	/*  NAVIGATION */ 
	
	/*$('#header div.mainNav > ul > li > div.subNav').each(function() {
		var thisSubnav = $(this);
		while(thisSubnav.children('ul:last').children('li').length > 4) {
			var curUL = thisSubnav.children('ul:last');
			curUL.after('<ul />');
			thisSubnav.children('ul:last').append(curUL.children(':gt(3)'));		
			curUL.children('li:last').css( { 'border-bottom' : '0' } );
		}
		thisSubnav.children('ul:last').children('li:last').css( { 'border-bottom' : '0' } );
	});
	
	$('#header div.mainNav > ul	> li').hover(function() {
		var currentLi = $(this);
		//currentLi.width(currentLi.width());
		//currentLi.height(currentLi.height());
		currentLi.addClass('active');
		currentLi.children('div.subNav').show();
		if(currentLi.children('div.subNav').length === 0) {
			currentLi.children('a').addClass('nosubnav');
		}
		
	},function() {
		var currentLi = $(this);
		currentLi.removeClass('active');
		currentLi.children('div.subNav').hide();
		currentLi.children('a').removeClass('nosubnav');
	});*/
	
	/* END NAVIGATION */
	


	
	/* MODULE FUNCTIONS */
	
	$('div.mod > div.mod_content > div.category > ul').each(function() {
		$(this).categoryList();
	});
	
	$('div.mod div.mod_content > ul > li').paintPadModule();

	$('div#photo_gallery_slot div#photo_gallery ul li:first').show();
	
	$('div#photo_gallery_slot div#photo_gallery a#photo_gallery_prev').click(function() {
		var visibleIndex = $('div#photo_gallery_slot div#photo_gallery ul li:visible').index();
		visibleIndex--;
		if(visibleIndex < 0) {
			visibleIndex = $('div#photo_gallery_slot div#photo_gallery ul li').length - 1;
		}
		$('div#photo_gallery_slot div#photo_gallery ul li').hide();
		$('div#photo_gallery_slot div#photo_gallery ul li:eq(' + visibleIndex + ')').show();
		return false;
	});
	
	$('div#photo_gallery_slot div#photo_gallery a#photo_gallery_next').click(function() {
		var visibleIndex = $('div#photo_gallery_slot div#photo_gallery ul li:visible').index();
		visibleIndex++;
		visibleIndex %= $('div#photo_gallery_slot div#photo_gallery ul li').length;
		$('div#photo_gallery_slot div#photo_gallery ul li').hide();
		$('div#photo_gallery_slot div#photo_gallery ul li:eq(' + visibleIndex + ')').show();
		return false;
	});
	
		
		/* GLOBAL TABS */
		
		var globalTabs = setInterval(function() {
			$('.tabs_rotate').each(function(){
				$(this).children('.global_tabs_nav').children('li').each(function () {
						
					var currentLi = $(this);
					var allSlides = $(this).parent().parent().find('.global_tabs_slides');
					var currentSlide = allSlides.children('li:visible')
					
					if(currentLi.hasClass('active')) {
						currentLi.removeClass('active');
						currentLi.next().addClass('active');
							
						if(currentLi.next().size()) {
							currentLi.next().addClass('active');
							allSlides.children('li').hide();
							currentSlide.next().show();
						} else {
							currentLi.parent().children().first().addClass('active');
							currentSlide.hide();
							allSlides.children().first().show();
						}
						return false
					}
				}); 
			});
		 }, 8000);
		
		
		$('.global_tabs_nav > li').click(function () {
			clearInterval(globalTabs);
			var thisLi = $(this);
			var thisSlide = $(this).parent().parent().find('.global_tabs_slides');
			thisLi.siblings().removeClass('active');
			thisLi.addClass('active');
			thisSlide.children('li').hide();
			thisSlide.children('li:eq(' + thisLi.index() + ')').show();
			var isFrame = $(thisSlide.children('li:eq(' + thisLi.index() + ')')).find('iframe');
			if (isFrame.length) {
			    var isFrameSrc = $(isFrame).attr('src');
			    $(isFrame).attr('src',isFrameSrc);
			}
		});
		$('.global_tabs_nav').each(function(){
			if(!$(this).children('li').hasClass('active')){
				$(this).children('li:first').click();
			}
		});
		

		
		
		/* END GLOBAL TABS */	
	
	/* END MODULE FUNCTIONS */
	
	/* FOOTER FUNCTIONS */
	
	$('div#footer_slot div#footer div#footer_info ul#footer_links li').each(function() {
		var currentLi = $(this);
		var prevLi = currentLi.prev();
		if(prevLi.text()) {
			currentLi.before('<li>|</li>');
			var divider = currentLi.prev();
			var curOffset = currentLi.offset();
			var prevOffset = prevLi.offset();
			var divOffset = divider.offset();
			if(curOffset.top !== prevOffset.top) {
				if(divOffset.top === prevOffset.top) {
					divider.css({ 'visibility' : 'hidden' });
				}
				else {
					divider.css({ 'display' : 'none' });
				}
			}
		}
	});

	
	/* END FOOTER FUNCTIONS */
	
	/* CALENDAR */
		$('#calendarPageTitle').append($('div.primaryc h3'));
	/* END CALENDAR */
	
	/* MULTIMEDIA */
	
		/* STARS */
		$('#video_info ul.keywords li:not(:last)').append(',&nbsp;');
		$('#video_info div.view_info').after('<div class="separator"> |</div>');
		$('#video_info div.rating_info').stars();
		/* END STARS */
		
		/* TOP VIDEOS TABS */
		$('ul#top_videos').before('<ul id="top_videos_nav" />');
		$('ul#top_videos > li > h4').each(function() {
			var curH4 = $(this);
			$('ul#top_videos_nav').append(curH4);
			curH4.wrap('<li />');
		});
		$('ul#top_videos > li').addClass('top_video_tab');
		$('ul#top_videos_nav > li').click(function () {
			var thisLi = $(this);
			thisLi.siblings().removeClass('active');
			thisLi.addClass('active');
			$('ul#top_videos > li').hide();
			$('ul#top_videos > li:eq(' + thisLi.index() + ')').show();
			$('div#top_videos_wrap ul#top_videos > li > ul > li').paintPadModule();
		});
		$('ul#top_videos_nav > li:first').click();
		/* END TOP VIDEOS TABS */
		
		
		
	/* END MULTIMEDIA */
	
	/* GALLERY */
	
		/* FEATURED GALLERY TABS */
			$('ul#featured_galleries').before('<ul id="top_galleries_nav" />');
			$('ul#featured_galleries > li > h4').each(function() {
				var curH4 = $(this);
				$('ul#top_galleries_nav').append(curH4);
				curH4.wrap('<li />');
			});
			$('ul#top_galleries_nav > li').click(function () {
				var thisLi = $(this);
				thisLi.siblings().removeClass('active');
				thisLi.addClass('active');
				$('ul#featured_galleries > li').hide();
				$('ul#featured_galleries > li:eq(' + thisLi.index() + ')').show();
				$('#one_column #main_content ul#featured_galleries li ul').equalHeights();
			});
			$('ul#top_galleries_nav > li:eq(1)').click();
		/* END FEATURED GALLERY TABS */
		
	/* END GALLERY */
	
	/*RULES TEST */
	if ($('#rules_list').length > 0){
		$('#rules_list').css('min-height','500px');	
		$('#rules_list > ul > li > ul').css('position', 'relative');
		$('#rules_list > ul > li').css('position', 'relative');
		$('#rules_list > ol > li > ol').css('position', 'relative');
		$('#rules_list > ol li').css('position', 'relative');
		
		//setting up page anchors to open the correct list item if hidden and then slide to location
		$("#rules_list a").each(function(i){
			var url = $(this).attr("href");
			if(url){
				if(url.indexOf("#") != -1 && url.indexOf("#") == 0){
					var redirect = false;
					var aRef = url.split("#",2);
					var aParts = aRef[1].split(".", 2);
					var anchor = $("li[id='"+aRef[1]+"']");
					if(anchor.length > 0){									
						$(this).click(function(){
							$('#rules_list ul > li#' + aParts[0] + ' > ul').slideDown('fast');
							$('#rules_list ol > li#' + aParts[0] + ' > ol').slideDown('fast');
							if ($('#rules_list ol > li#' + aParts[0] + ' > .expander').attr('class') != "expander clicked"){
								$('#rules_list ol > li#' + aParts[0] + ' > .expander').addClass('clicked');
							}
							if ($('#rules_list ul > li#' + aParts[0] + ' > .expander').attr('class') != "expander clicked"){
								$('#rules_list ul > li#' + aParts[0] + ' > .expander').addClass('clicked');
							}
							if($(document).height()-anchor.offset().top >= $(window).height()
							 || anchor.offset().top > $(window).height()
							 || $(document).width()-anchor.offset().left >= $(window).width()
							 || anchor.offset().left > $(window).width()){
											   
								$('html, body').animate({
									scrollTop: anchor.offset().top,
									scrollLeft: anchor.offset().left
								}, "normal", "swing", function(){
									if(redirect){ 
										window.location = url 
									}
								});
							}
							return false;							
						});
					}
						
				}
			}
		});
	}

	//list expanding and mouse functionality
	$('li .expander').css('cursor', 'pointer');
	$('li .expander').bind('click', function(){
		if ($(this).attr('class') != 'expander clicked'){
			$(this).siblings().slideDown("slow");
			$(this).addClass('clicked');
		} else {
			$(this).siblings().slideUp();
			$(this).removeClass('clicked');
		}
	});
	
	$('li .expander').hover(function(){
			$(this).css('background-color', '#ccc');
		}, function(){
			$(this).css('background-color', 'transparent');
	});
	
	//annotation sliding
	$('.annotation_item').css('cursor', 'pointer');
	$('.annotation_info').css('cursor', 'pointer');
	$('.annotation_item').bind('click', function(){
		if($(this).attr('class') != 'annotation_item clicked'){
			$(this).parent().find('.annotation_info').slideDown("fast");
			$(this).css('color', '#B20838');
			$(this).addClass('clicked');
		} else {
			$(this).parent().find('.annotation_info').slideUp("fast");
			$(this).css('color', '#000');
			$(this).removeClass('clicked');
		}
	});
	$('.annotation_info').click(function(){
		$(this).slideUp("fast");
		$(this).parent().find('.annotation_item').css('color', '#000');
		$(this).parent().find('.annotation_item').removeClass('clicked');	
	});
	
	//defintion popup functionality
	$('span.definition_item').hover(function(){
		var id = $(this).attr('id');
		var relation = id + "_info";
		var rel_info = $('#'+relation).html();
		var position = $(this).position();

		$(this).css('color', '#08245A');		
		$(this).parent().append('<div class="popup_info" style="top:'+(position.top + 20)+'px; left:'+ position.left +'px; height:auto;"></div>');
		$('.popup_info').html(rel_info);
		if ((position.left + $('.popup_info').width()) >= $(this).parent().width()){
			var move = position.left - ((position.left + $('.popup_info').width()) - $(this).parent().width());	
			$('.popup_info').css('left', move+'px');
		}
		if (($(this).offset().top + $('.popup_info').height()) >= $('#main_content').height()){
			var move = position.top - ((position.top + 60 + $('.popup_info').height()) - $(this).parent().height());	
			$('.popup_info').css('top', move+'px');
		}
		
	}, function(){
		$(this).css('color', '#0824DD');
		$('.popup_info').remove();
	});
	
	//Expanding all Items
	$('.expand_all a').bind('click', function(){
		if($('#rules_list').attr('class') != 'open'){
			$(this).html('Collapse All');
			$('.annotation_item').addClass('clicked');
			$('.annotation_item').css('color', '#B20838');
			$('.annotation_info').show();
			$('.expander').addClass('clicked');	
			$('.expander').siblings().slideDown();
			$('#rules_list').attr('class', 'open');
		} else {
			$(this).html('Expand All');
			$('.annotation_item').removeClass('clicked');
			$('.annotation_info').hide();
			$('.expander').removeClass('clicked');
			$('.expander').siblings().slideUp();
			$('#rules_list').attr('class', 'closed');
		}
		return false;
	});
	
	//initialize page depending on rules class
	if ($('#rules_list').length > 0){
		var path = window.location.hash;
		if (($('#rules_list').attr('class') == 'open') || path.length > 0){
			$('.expand_all a').html('Collapse All');
			$('.annotation_item').addClass('clicked');
			$('.annotation_item').css('color', '#B20838');
			$('.annotation_info').show();
			$('.expander').addClass('clicked');	
			$('.expander').siblings().show();
			$('#rules_list').attr('class', 'open');
		} else {	
			$('#rules_list > ul > li > ul').hide();	
			$('#rules_list > ol > li > ol').hide();	
			$('.expand_all a').html('Expand All');
		}	
		
		//Open Closed Items if user hits ctrl+f
		$(document).keydown(function (e) { 
			if(e.keyCode == 70 && e.ctrlKey) {
				$('.expand_all a').html('Collapse All');
				$('.annotation_item').addClass('clicked');
				$('.annotation_item').css('color', '#B20838');
				$('.annotation_info').show();
				$('.expander').addClass('clicked');	
				$('.expander').siblings().slideDown();
			}
		}); 		
	}
	/*END RULES TEST*/
	
});


$(window).load(function() {
	/* TEMPLATE FUNCTIONS */
		
	var railHeight = $('#two_column > #rail').height();
	var mainHeight = $('#two_column > #mainCol').height();
	if(railHeight > mainHeight) {
		$('#two_column > #mainCol').css('min-height', railHeight);
		$('#two_column > #mainCol').css('height', railHeight);
	}
	
	/* END TEMPLATE FUNCTIONS */
	
	
	var maxVidLiHeight = 0;
	$('div#other_video_wrap > div#other_videos > ul#videos > li').each(function() {
		var liHeight = $(this).height();
		if(liHeight > maxVidLiHeight) {
			maxVidLiHeight = liHeight;
		}
	});
	var maxGalleryLiHeight = 0;
	$('#other_gallery_wrap > #other_galleries > ul#galleries > li').each(function() {
		var liHeight = $(this).height();
		if(liHeight > maxGalleryLiHeight) {
			maxVidLiHeight = liHeight;
		}
	});
	//$('div#multimedia > div#other_video_wrap > div#other_videos > ul#videos > li').height(maxVidLiHeight);
	$('#other_gallery_wrap > #other_galleries > ul#galleries > li').height(maxGalleryLiHeight);

	if ($('div#stories').length > 0 ) {
		$('div#stories ul#homepage_rotator > li:eq(4) > div > h3 > a').changeStory();
	}
	

})

jQuery.fn.paintPadModule = function() {

var thisList = $(this);
thisList.each(function() {
		var thisLi = $(this);
		if(thisLi.index() % 2 === 0) {
			thisLi.css({'background' : '#0b305b' });
		}
		var liHeight = thisLi.height();
		var aHeight = thisLi.children('a').height();
		var dateHeight = thisLi.children('div.date').height();
		var eventHeight = thisLi.children('div.event').height();
		if(eventHeight > dateHeight) {
			thisLi.children('div.date').height(eventHeight);
			dateHeight = eventHeight;
		}
		if(dateHeight > eventHeight) {
			thisLi.children('div.event').height(dateHeight);
			eventHeight = dateHeight;
		}
		var padding = Math.floor((liHeight - aHeight) / 2);
		thisLi.children('a').css({'padding-top' : padding, 'padding-bottom' : padding});
		var eventPadding = Math.floor((liHeight - eventHeight) / 2);
		thisLi.children('div.date').css({'padding-top' : eventPadding, 'padding-bottom' : eventPadding});
		thisLi.children('div.event').css({'padding-top' : eventPadding, 'padding-bottom' : eventPadding});
	});

};

jQuery.fn.loadMultimediaInfo = function() {
	/* OTHER VIDEOS TABS */
		$('div#other_video_wrap > div#other_videos > div#video_category > ul').each(function() {
			$(this).categoryList();
		});
		$('div#other_video_wrap > div#other_videos > ul#videos > li > div.view_info').after('<div class="separator">|</div>');
		$('div#other_video_wrap > div#other_videos > ul#videos > li > div.rating_info').each(function() {
			var starCount = parseFloat($(this).children('div.rating').text());
			$(this).children('div.rating').width(starCount * 10.0);
		});
		//$('div#multimedia > div#other_video_wrap > div#other_videos > ul#videos').after('<div id="video_navigation" />');
		//$('div#multimedia > div#other_video_wrap > div#other_videos > div#video_navigation').append('<div id="video_count">Clips 1 - 8 out of 30</div>');
		//$('div#multimedia > div#other_video_wrap > div#other_videos > div#video_navigation').append('<div id="video_paging"><span class="prev">Previous</span> | <a href="#" class="next">Next</a></div>');
		
		
		/* END OTHER VIDEOS TABS */
	
}

jQuery.fn.categoryList = function() {
	var thisList = $(this);
	thisList.before($('<div class="dropdown_selector">&nbsp;</div>'));
	thisList.siblings('div.dropdown_selector').text(thisList.find('a.selected').text());
	thisList.siblings('div.dropdown_selector').click(function(event) {
		event.preventDefault();
		$(this).siblings('ul').toggle();
	});
	thisList.find('li > a').click(function(event) {
		var curLink = $(this);
		var curLi = curLink.parent();
		var curList = curLi.parent();		
		event.preventDefault();
		curLi.siblings().children('a').removeClass('selected');
		curLink.addClass('selected');
		curList.siblings('div.dropdown_selector').text(curLink.text());
		var listIndex = curLi.index();
		curList.hide();
		var categoryWrap = curList.parents('div.category');
		categoryWrap.siblings('ul').hide();
		categoryWrap.siblings('ul:eq(' + listIndex + ')').show();
		
		var storyItems = categoryWrap.siblings('ul:visible').children('li');
		
		storyItems.paintPadModule();
	});
}

jQuery.fn.stars = function() {
	var starWrap = $(this);
	var stars = starWrap.children('div.rating');
	var rating = parseFloat(stars.text());

	if (stars.text() === ''){

		rating = 0;

	}

	var ratingWidth = parseInt(rating * 16);

	stars.width(ratingWidth);
	stars.after('<ul />');
	var starsList = starWrap.children('ul');
	for(i=0; i<5; i++) {
		starsList.append('<li />');
	}
	var hasbeenClicked = false;
	starsList.children('li').hover( function() {
		if (hasbeenClicked === false){
			var thisLi = $(this);
			thisLi.css({'background' : 'url(/cms/images/buttons/lg_star.png) top left no-repeat'})
			var thisLiIndex = thisLi.index();
			thisLi.parent().children(':lt(' + thisLiIndex + ')').css({'background' : 'url(/cms/images/buttons/lg_star.png) top left no-repeat'})
			thisLi.parent().children(':gt(' + thisLiIndex + ')').css({'background' : 'url(/cms/images/buttons/lg_star.png) bottom left no-repeat'})
		}
	},function() {
		if (hasbeenClicked === false){
			var thisLi = $(this);
			thisLi.parent().children().css({'background' : 'transparent'})
		}
	}).click(function() {
		if (hasbeenClicked === false){
			var thisLi = $(this);
			//alert(thisLi.index());
			var userRating = thisLi.index() + 1;
			videoRating($('#videoId').val(), userRating, "");
			stars.width(userRating * 16);
			hasbeenClicked = true;
		}
	});
	
}
var isPlayed = false;
jQuery.fn.playVideo_new = function() {
		var storyArea = $(this);
		var video_storyID = $('ul#homepage_rotator li.active').find('div.video').attr('name');
		var videoID = $('div#stories div#story_area div.#' + video_storyID ).children().attr('id');
		$('div#stories div#story_area img').hide();		
		$('div#stories div#story_area div.play_video').hide();
		$('div#stories div#story_area div.image_overlay').hide();
		$('div#stories div#story_area div.#' + video_storyID).show();
		$('div#stories div#story_area a.play_video').hide();
		$('div#stories div#story_area a.close_video').show();
		storyInterval = clearInterval(storyInterval);
		$('ul#homepage_rotator li.active div.activator').addClass('deactivated').removeClass('activator');
		$('div#home div#stories ul#homepage_rotator li.active').css({'z-index' : '0'});
		$('div#home div#stories div#story_area').css({'z-index' : '20'});
		if (isPlayed != false){
			restartVideo(videoID);
			playVideo(videoID);
		}
		return false;
}

jQuery.fn.closeVideo = function() {
		//var storyArea = $(this);
		var video_storyID = $('ul#homepage_rotator li.active').find('div.video').attr('name');
		var videoID = $('div#stories div#story_area div.#' + video_storyID ).children().attr('id');
		$('div#stories div#story_area div.#' + video_storyID).hide();
		$('div#stories div#story_area div.image_overlay').show();
		$('div#stories div#story_area img').show();	
		$('div#stories div#story_area div.play_video').show();
		$('div#stories div#story_area a.play_video').show();
		$('div#stories div#story_area a.close_video').hide();
		$('ul#homepage_rotator li.active div.deactivated').addClass('activator').removeClass('deactivated');
		$('div#home div#stories ul#homepage_rotator li.active').css({'z-index' : '19'});
		$('div#home div#stories div#story_area').css({'z-index' : '15'});
		stopVideo(videoID);
		isPlayed = true;
		return false;
}
jQuery.fn.changeStory = function() {
	var thisLink = $(this);
	var thisLi = $(this).parent().parent().parent();
	var totalLis = thisLi.parent().children().length;
	var offset = (thisLi.index() + 2) % totalLis;
	var moveChildren = thisLi.parent().children(':lt(' + offset + ')');
	
	

	thisLi.parent().append(moveChildren);
	$('div#stories div#story_area').closeVideo();
	$('div#stories ul#homepage_rotator > li').removeClass('active');
	$('div#stories ul#homepage_rotator > li > div > h3').paintRotator();
	$('div#stories ul#homepage_rotator > li:eq(4)').addClass('active');
	$('div#stories ul#homepage_rotator > li > div > h3 > a').padRotator();
	
	$('div#stories div#story_area div#story_info').empty();
	$('div#stories div#story_area div#story_info').append(thisLi.find('img.article_image').clone());
	$('div#stories div#story_area div#story_info').append(thisLi.find('div.summary').clone());
	$('div#stories div#story_area div#story_info').append(thisLi.find('h3 a').clone().addClass('full_story'));

	$('div#stories div#story_area div#story_info').append('<div class="image_overlay">&nbsp</div>');
	$('div#stories div#story_area div#story_info a.full_story').css({ 'padding-top' : '0px', 'padding-bottom' : '0px' });
	$('div#stories div#story_area div#story_info a.full_story').html('<span>Read the Full Story</span>');
	if ($('div#stories div#story_area div#story_info a.full_story').attr('rel') == "gallery"){
		$('div#stories div#story_area div#story_info a.full_story').html('<span>View Gallery</span>');
	}
	if(thisLi.find('div.video').length > 0) {
		$('div#stories div#story_area a.full_story').html('<span>Watch Video</span>');
		$('div#stories div#story_area a.full_story').addClass('play_video').unbind().bind('click', function(event) {
			$('div#stories div#story_area').playVideo_new();
			event.preventDefault();
		});
		$('div#stories div#story_area .article_image').addClass('play_video').bind('click', function() {
			$('div#stories div#story_area').playVideo_new();
		});
		//$('div#stories div#story_area').append('<div class="video" style="display:none;"/>');
		//$('div#stories div#story_area').append(thisLi.find('div.video').html());
		$('div#stories div#story_area div#story_info').append('<div class="play_video">Play Video</div>');
		$('div#stories div#story_area .play_video').bind('click', function() {
			$('div#stories div#story_area').playVideo_new();
		});
		$('div#stories div#story_area div#story_info').append('<a href="#" class="full_story close_video"><span>Close Video</span></a>');
		$('div#stories div#story_area .close_video').hide().bind('click', function() {
			$('div#stories div#story_area').closeVideo();
		});
		$('div#stories ul#homepage_rotator > li.active > div.deactivated').removeClass('deactivated').addClass('activator');
	}

	if (thisLi.find('.videoEmbed').length > 0){
		$('div#stories div#story_area div#story_info').empty();
		$('div#stories div#story_area div#story_info').append(thisLi.find('div.videoEmbed').clone());
	} else {

	}
	$('div#home div#stories ul#homepage_rotator li.active').css({'z-index' : '19'});
	$('div#home div#stories div#story_area').css({'z-index' : '15'});
}

jQuery.fn.paintRotator = function() {
	var walls = $(this);
	if(walls.length > 1) {
		walls.css({ 'background' : 'transparent' });
		var active = walls.length - 2;
		walls.filter(':lt(' + active + ')').each(function(index) {
			if((index % 2) === 0) {
				$(this).css({ 'background-color' : '#0b305b'});
			}
			else {
				$(this).css({ 'background-color' : '#062140'});
			}
		});
		
		walls.filter(':gt(' + (active) + ')').each(function(index) {
			if((index % 2) === 0) {
				$(this).css({ 'background-color' : '#0b305b'});
			}
			else {
				$(this).css({ 'background-color' : '#062140'});
			}
		});
	}
	return false;
};

jQuery.fn.padRotator = function() {
	var links = $(this);
	$(this).each(function(index, value) {
		var rotator_link = $(this);
		var rotator_parent = $(this).parent();
		var padding = Math.floor((rotator_parent.height() - rotator_link.height()) / 2);
		if(padding > 0) {
			rotator_link.css({ 'padding-top' : padding + 'px', 'padding-bottom' : padding + 'px' });
		}
	});
};




