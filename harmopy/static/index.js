load = function(url, id) {
    // Load the json into the template and append it to the elem
    var template = Handlebars.compile($(id + '-template').html());
    $.get(url, function(data){
        $.each([].concat(data), function(i, elem) {
            console.log(elem);
            var html = template(elem);
            console.log(html);
            $(id + ' .loading').hide();
            $(id + ' .data').append(html);
            $(id + ' .showondata').removeClass('hidden');
        });
    });
}
$(document).ready(function() {
    load('/status', '#status');
    load('/history', '#history');
    load('/config', '#config');
    load('/files', '#files');
});
