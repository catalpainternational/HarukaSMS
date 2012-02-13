function submitForm(link, action, resultDiv) {
    form = $(link).parents("form");
    form_data = form.serializeArray();
    resultDiv.load(action, form_data);
}


$(document).ready(function() {
	//Accordion based messaging history list
    if($('#accordion').length > 0) {
    	$(function() {
    		$( "#accordion" ).accordion({ autoHeight: false, collapsible: true });
    	});
    }
	$(function() {    		
        $('.replyForm').hide();
	});
});


function collapse() {
    $('#show_results_list').show();
    $('#object_list').hide();
}


function expand() {
    $('#show_results_list').hide();
    $('#object_list').show();
}


function toggleReplyBox(anchor, phone, msg_id){
    anchor.innerHTML = (anchor.text == '- send message -')? '- hide message box -' : '- send message -';
    var _currentDiv = document.getElementById('replyForm_'+msg_id);
    $(_currentDiv).append($('#formcontent'));
    $('#formcontent').show();
    $(_currentDiv).slideToggle(300);
    $('#id_recipient').val(phone);
    $('#id_in_response_to').val(msg_id);
}