var $j = jQuery.noConflict();
$j(document).ready(function() {
	if (!$j('#watermark').val()) {
		$j('#watermark').css({"background": "white url('/static/images/google_watermark.gif') no-repeat left center"});
		$j('.inputalign > #watermark').css({"background": "white url('/static/images/google_watermark.gif') no-repeat 15px center"});
	}
	// special case for search box which is repeated on empty search results page
	if (!$j('#watermarkempty').val()) {
		$j('#watermarkempty').css({"background": "white url('/static/images/google_watermark.gif') no-repeat 15px center"});
	}
});
