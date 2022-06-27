// <!-- This goes in the head -->
// <!-- Google Tag Manager -->
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-NR2RWK5');
// <!-- End Google Tag Manager -->

// <!-- This goes in the body -->
document.addEventListener("DOMContentLoaded", function(event) {
    var firstBodyDiv = document.body.childNodes[0];

    var gtmScript   = document.createElement("script");
    gtmScript.type  = "text/javascript";
    gtmScript.text  = '<!-- Google Tag Manager (noscript) -->'; // inline script
    gtmScript.text += '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NR2RWK5"';
    gtmScript.text += 'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>';
    gtmScript.text += '<!-- End Google Tag Manager (noscript) -->';
    firstBodyDiv.before(gtmScript);
});
