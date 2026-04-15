.. _documentation_footer:

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
          } else if (docLanguage == "ko") {
              if (str == "Find <b>#pymupdf</b> on <b>Discord</b>") {
                  return "<b>Discord</b> 에서 <b>#pymupdf</b> 찾기";
              } else if (str == "Have a <b>&nbsp;question</b>? Need some <b>&nbsp;answers</b>?&nbsp;") {
                  return "<b>&nbsp;질문</b>이 있으신가요? <b>&nbsp;답변</b>이 필요하신가요?&nbsp;";
              }
              else if (str == "This software is provided AS-IS with no warranty, either express or implied. This software is distributed under license and may not be copied, modified or distributed except as expressly authorized under the terms of that license. Refer to licensing information at <a href='https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link'>artifex.com</a> or contact Artifex Software Inc., 39 Mesa Street, Suite 108A, San Francisco CA 94129, United States for further information.") {
                  return "이 소프트웨어는 명시적이든 묵시적이든 어떠한 보증도 없이 있는 그대로 제공됩니다. 이 소프트웨어는 라이선스에 따라 배포되며, 해당 라이선스 조건에 명시적으로 승인된 경우를 제외하고는 복사, 수정 또는 배포할 수 없습니다. 라이선스 정보는 <a href='https://www.artifex.com?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=footer-link'>artifex.com</a> 에서 참조하거나, 미국 캘리포니아주 샌프란시스코 Mesa Street 39, Suite 108A 소재 Artifex Software Inc. 에 문의하시기 바랍니다."
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

