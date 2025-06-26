----

.. raw:: html

   <p style="color:#999" id="footerDisclaimer">This software is provided AS-IS with no warranty, either express or implied. This software is distributed under license and may not be copied, modified or distributed except as expressly authorized under the terms of that license. Refer to licensing information at <a href="https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link">artifex.com</a> or contact Artifex Software Inc., 39 Mesa Street, Suite 108A, San Francisco CA 94129, United States for further information.</p>

   <script>

      let docLanguage = document.getElementsByTagName('html')[0].getAttribute('lang');

      function getHeaderAndFooterTranslation(str) {
          if (docLanguage == "ja") {
              if (str == "Find <b>#pymupdf</b> on <b>Discord</b>") {
                  return "<b>Discord</b>の <b>#pymupdf</b> を見つける";
              } else if (str == "Have a <b>&nbsp;question</b>? Need some <b>&nbsp;answers</b>?&nbsp;") {
                  return "質問がありますか？答えが必要ですか？";
              }
              else if (str == "This software is provided AS-IS with no warranty, either express or implied. This software is distributed under license and may not be copied, modified or distributed except as expressly authorized under the terms of that license. Refer to licensing information at <a href='https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link'>artifex.com</a> or contact Artifex Software Inc., 39 Mesa Street, Suite 108A, San Francisco CA 94129, United States for further information.") {

                  return "このソフトウェアは無保証で提供されており、明示または黙示を問わず、いかなる保証もありません。このソフトウェアはライセンスの下で配布され、ライセンスの条件に明示的に許可されている場合を除き、コピー、変更、または配布してはなりません。ライセンシング情報については、<a href='https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link'>artifex.com</a>でライセンス情報を参照するか、アメリカ合衆国カリフォルニア州サンフランシスコのArtifex Software Inc. までお問い合わせください。"

              }
          }

          return str;
      }

      document.getElementById("findOnDiscord").innerHTML = getHeaderAndFooterTranslation("Find <b>#pymupdf</b> on <b>Discord</b>");
      document.getElementById("forumCTAText").innerHTML = getHeaderAndFooterTranslation("Have a <b>&nbsp;question</b>? Need some <b>&nbsp;answers</b>?&nbsp;");
      document.getElementById("footerDisclaimer").innerHTML = getHeaderAndFooterTranslation("This software is provided AS-IS with no warranty, either express or implied. This software is distributed under license and may not be copied, modified or distributed except as expressly authorized under the terms of that license. Refer to licensing information at <a href='https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link'>artifex.com</a> or contact Artifex Software Inc., 39 Mesa Street, Suite 108A, San Francisco CA 94129, United States for further information.");


      // more translation for admonition-title as the in-built translation isn't great, needs: 注釈 -> 注
      if (docLanguage == "ja") {
          const collection = document.getElementsByClassName("admonition-title");
          for (var i=0;i<collection.length;i++) {
              collection[i].innerHTML = "注";
          }
      }


   </script>

.. rst-class:: footer-version

  This documentation covers all versions up to |version|.


.. External Links:

.. _pdf2docx: https://pdf2docx.readthedocs.io/en/latest/
.. _pdf2docx extract tables method: https://pdf2docx.readthedocs.io/en/latest/quickstart.table.html

