var access_token;

function urlParam(url, name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(url);
    return results[1] || 0;
}

function selectAll(){
	$('#modules-form').find(':checkbox').attr('checked', true);
	return false;
}

function selectNone(){
	$('#modules-form').find(':checkbox').attr('checked', false);
	return false;
}

function handleProgrammeForm(){
	form_data = $('#programmes-form').serialize();
	url = 'http://' + location.host + '/select_modules?' + form_data;

	$('#loading-space').addClass('loading');
	$('#editable').html('');
	if(urlParam(url, 'programme_code').indexOf('BA') == 0){
		$('#editable').append('<p>LOL Arts</p>');
	}
	$('#editable').append('<p>Please wait, parsing your programme and loading modules...</p>');
	$.get(url, function(data) {
		$('#editable').html(data);
		$('#submit').click(handleModulesForm);
		$('#select-all').click(selectAll);
		$('#select-none').click(selectNone);
		$('#loading-space').removeClass('loading');
	});
	return false;
}

function handleModulesForm(){
	form_data = $('#modules-form').serialize();
	url = 'http://' + location.host + '/finalize?' + form_data + '&access_token=' + access_token;
	
	$('#loading-space').addClass('loading');
	$('#editable').html('');
	$('#editable').append('<p>Please wait, putting everything into your calander. This might take a while.</p>');
	$.get(url, function(data) {
		$('#editable').html(data);
		$('#loading-space').removeClass('loading');
	});
	return false;
}

$(document).ready(function(){
	access_token = urlParam(window.location.href, 'access_token');
	$('#programmes-form').submit(handleProgrammeForm);
});