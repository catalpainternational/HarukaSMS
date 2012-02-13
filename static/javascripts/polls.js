function deletePoll(link, poll_action, poll_name) {
    if (confirm("Are you sure you want to delete \"" + poll_name + "\" ?")) {
        $.post(poll_action, function(data) {
           $(link).parents("tr").remove();
        });
    }
}
