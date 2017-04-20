(function (win, $) {
  'use strict';

  var TOC_NAV_WIDTH = 350;
  var toggle = null;
  var contenteditor = null;

  function openNav(id) {
    $('#' + id).width(TOC_NAV_WIDTH);
    toggle.find('span.showToc').first().addClass('hide');
    toggle.find('span.hideToc').first().removeClass('hide');
    toggle.removeClass('closed');
    toggle.addClass('opened');
  }

  function closeNav(id) {
    $('#' + id).width(0);
    toggle.find('span.hideToc').first().addClass('hide');
    toggle.find('span.showToc').first().removeClass('hide');
    toggle.removeClass('opened');
    toggle.addClass('closed');
  }

  function toggleNav(id) {
    if (toggle.hasClass('opened')) {
      closeNav(id);
    } else {
      openNav(id);
    }
  }

  // document ready
  $(function () {
    toggle = $('#toctoggle');
    contenteditor = $('#contenteditor');

    // load custom theme
    var embeduserstyle = $("#embeduserstyle");
    if (embeduserstyle.length) {
      var cssTemplate = _.template($('#embedUserStyleTemplate').html());
      // themeCustom variable is defined in fullview.html
      // sorry for this :(
      embeduserstyle.text(cssTemplate(themeCustom));
    }

    // add toc show/hide handler
    contenteditor.on('click', function () {
      if (toggle.hasClass('opened')) {
        closeNav('ToCslider');
      }
    });

    toggle.on('click', function () {
      toggleNav('ToCslider');
    });

    $('.closebtn').on('click', function () {
      closeNav('ToCslider');
    });

    $("#ToCslider").mCustomScrollbar({
      theme: 'dark-thick',
      alwaysShowScrollbar: 0,
      scrollButtons: {
        enable: true,
        scrollAmount: 250,
        scrollType: 'stepped'
      }
    });

    // handle links
    $('p a[href^="../"]', contenteditor).each(function () {
      var $a = $(this);
      var chapterSlug = $a.attr('href').split('/')[1];

      if ($('a.chapter_link[href="#' + chapterSlug + '"]').length) {
        $a.addClass('chapter_link');
        $a.attr('href', '#' + chapterSlug);
      } else {
        $a.removeAttr('href');
      }
    });

    // enable kind of softly scroll
    $('.chapter_link').click(function () {
      $('html, body').animate({
        scrollTop: $($.attr(this, 'href')).offset().top - 120
      }, 1000);
    });

    // change html to have better fit with editor.css
    $('div.chapter-inner', contenteditor).each(function () {

      var chapterInner = $(this);

      // wrap chapter title headings with div
      $('h1', chapterInner).first().wrap("<div class='aloha-block-TitleBlock'></div>");

      // handle multicolumns
      $('div.bk-columns', chapterInner).each(function () {
        var $this = $(this);
        var columnCount = $this.attr('data-column');
        var columnGap = $this.attr('data-gap') + 'mm';

        $this.css('column-count', columnCount);
        $this.css('-webkit-column-count', columnCount);
        $this.css('-moz-column-count', columnCount);

        $this.css('column-gap', columnGap);
        $this.css('-webkit-column-gap', columnGap);
        $this.css('-moz-column-gap', columnGap);
      });

      // handle images
      $('div.group_img', chapterInner).each(function () {
        var $divCaptionWrapper = null;
        var $divGroupImg = $(this);
        var $divCaptionSmall = $divGroupImg.find('div.caption_small');

        if ($divCaptionSmall.length === 0) {
          var $pCaptionSmall = $divGroupImg.find('p.caption_small');

          // convert old formated caption_small to new format using div
          if ($pCaptionSmall.length && $pCaptionSmall.html().length) {
            $divCaptionSmall = $('<div class="caption_small">' + $pCaptionSmall.html() + '</div>');
            $divCaptionWrapper = $('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
            $pCaptionSmall.replaceWith($divCaptionWrapper);
          }

        } else {
          // convert new style caption_small with div
          $divCaptionWrapper = $('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
          $divCaptionSmall.replaceWith($divCaptionWrapper);
        }
      });

      win.booktype.utils.bkImageEditorScaleImages(chapterInner, chapterInner.width());

      $(window).resize(function () {
        win.booktype.utils.bkImageEditorScaleImages(chapterInner, chapterInner.width());
      });
    });

  });

})(window, $);
