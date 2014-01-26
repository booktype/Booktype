define ['aloha', 'aloha/plugin', 'jquery', 'css!../../../oer/mathcheatsheet/css/mathcheatsheet.css'], (Aloha, Plugin, $) ->
  Plugin.create "mathcheatsheet",
    defaultSettings: {}
    init: ->
      @settings = $.extend(true, @defaultSettings, @settings)

      # Modify math editor popover
      Aloha.require ['math/math-plugin'], (MathPlugin) ->
        MathPlugin.editor.find('.math-container').before '''
            <div class="math-help-link">
                <a title="Help using the math editor"
                   href="javascript:;">See help</a>
            </div>'''
        MathPlugin.editor.find('.plaintext-label').after '''
            <label class="cheatsheet-label checkbox inline">
                <input id="cheatsheet-activator" type="checkbox" name="cheatsheet-activator"> Show cheat sheet
            </label>'''
        MathPlugin.editor.find('#cheatsheet-activator').on 'change', (e) ->
          if jQuery(e.target).is(':checked')
            jQuery('#math-cheatsheet').trigger "show"
          else
            jQuery('#math-cheatsheet').trigger "hide"

        MathPlugin.editor.find('.math-help-link a').on 'click', (e) ->
          HELP_TEMPLATE = '<div class="popover math-editor-help-text"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"></div></div></div>'
          $h = jQuery(@)
          $h.unbind 'click'
          jQuery.get(Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/lib/help.html', (d) ->
            $h.popover(
              content: d,
              placement: 'right'
              html: true
              template: HELP_TEMPLATE
            ).on('shown-popover', (e)->
              jQuery(e.target).data('popover').$tip.find('.math-editor-help-text-close').on 'click', () ->
                jQuery(e.target).popover('hide')
              jQuery(e.target).data('popover').$tip.find('.cheatsheet-activator').on 'click', (e) ->
                jQuery('#math-cheatsheet').trigger "toggle"
            ).popover('show')
          )

      help = jQuery('''
        <div id="math-cheatsheet">
          <div class="cheatsheet-open">
            <img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/open-cheat-sheet-01.png' + '''" alt="open" />
          </div>
          <div class="cheatsheet">
            <div class="cheatsheet-close">
              <img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/close-cheat-sheet-01.png' + '''" alt="open" />
            </div>
            <div class="cheatsheet-title"><strong>Math Cheat Sheet</strong>: Copy the "code" that matches the display you want. Paste it into the math entry box above. Adjust as needed.</div>
            <div class="cheatsheet-type">
              <div><input type="radio" name="cs-math-type" id="cs_radio_ascii" value="ascii" checked="checked"> <label for="cs_radio_ascii">ASCIIMath</label></div>
              <div><input type="radio" name="cs-math-type" id="cs_radio_latex" value="latex"> <label for="cs_radio_latex">LaTeX</label></div>
            </div>
            <div class="cheatsheet-values cheatsheet-ascii">
              <table>
                <tr>
                  <td><strong>Display:</strong></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/root2over2.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/pirsq.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/xltoet0.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/infinity.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/aplusxover2.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/choose.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/integral.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/function-01.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/matrix-01.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/sin-01.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/piecewise-01.gif' + '''" /></td>
                  <td><img src="''' + Aloha.settings.baseUrl + '/../plugins/oer/mathcheatsheet/img/standard-product-01.gif' + '''" /></td>
                </tr>
                <tr>
                  <td><strong>ASCIIMath code:</strong></td>
                  <td>sqrt(2)/2</td>
                  <td>pir^2  or  pi r^2</td>
                  <td>x &lt;= 0</td>
                  <td>x -&gt; oo</td>
                  <td>((A+X)/2 , (B+Y)/2)</td>
                  <td>sum_{k=0}^{s-1} ((n),(k))</td>
                  <td>int_-2^2 4-x^2dx</td>
                  <td>d/dxf(x)=lim_(h-&gt;0)(f(x+h)-f(x))/h</td>
                  <td>[[a,b],[c,d]]((n),(k))</td>
                  <td>sin^-1(x)</td>
                  <td>x/x={(1,if x!=0),(text{undefined},if x=0):}</td>
                  <td>((a*b))/c</td>
                </tr>
              </table>
            </div>
            <div class="cheatsheet-values cheatsheet-latex">TODO<br /><br /><br /><br /><br /><br /></div>
            <div style="clear: both"></div>
          </div>
        </div>
      ''')
      jQuery('body').append(help)
      opener = help.find('.cheatsheet-open')
      
      help.on 'show', (e) ->
        opener.hide()
        # It says slideDown, but it really causes it to slid up.
        jQuery(@).find('.cheatsheet').slideDown "fast"
      
      help.on 'hide', (e) ->
        jQuery(@).find('.cheatsheet').slideUp "fast", () ->
            opener.show('slow')

      help.on 'toggle', (e) ->
        if jQuery(@).find('.cheatsheet').is(':visible')
          jQuery(@).trigger 'hide'
        else
          jQuery(@).trigger 'show'
      
      opener.on 'click', (e) ->
        help.trigger 'show'
        # Tick the cheat sheet activator tickbox
        jQuery('body > .popover .math-editor-dialog #cheatsheet-activator').prop('checked', true)
      
      help.find('.cheatsheet-close').on "click", (e) ->
        help.trigger "hide"
        # Untick activator
        jQuery('body > .popover .math-editor-dialog #cheatsheet-activator').prop('checked', false)
      
      help.find('.cheatsheet-type input').on "change", (e) ->
        sh = jQuery(e.target).val()
        help.find('.cheatsheet-ascii').hide()
        help.find('.cheatsheet-latex').hide()
        help.find(".cheatsheet-#{sh}").show()
      help.on 'mousedown', (e) ->
        # Stop the click from bubbling up and closing the math plugin
        e.stopPropagation()

      # Delegated events to hide and show the opener element
      jQuery('body').on 'shown-popover', '.math-element', () ->
        jQuery('#math-cheatsheet .cheatsheet-open').show()
      jQuery('body').on 'hide-popover', '.math-element', (e) ->
        jQuery(e.target).data('popover').$tip.find('.math-help-link a').popover('destroy')
        jQuery('#math-cheatsheet .cheatsheet-open').hide()

    toString: ->
      "mathcheatsheet"
