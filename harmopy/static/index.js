var store = {
    status: [],
    history: [],
    config: [],
    files: []
};

load = function(id) {
    // Load the json into the template and append it to the elem
    var template = Handlebars.compile($('#' + id + '-template').html());
    $.get('/' + id, function(data){
        $.each([].concat(data), function(i, elem) {
            store[id][elem.id] = elem;
            var html = template(elem);
            $('#' + id + ' .loading').hide();
            $('#' + id + ' .data').append(html);
            $('#' + id + ' .showondata').removeClass('hidden');
        });
        $('.confirm-file-delete').click(function() {
            console.log($(this).data('id'));
            $('#modal').modal({backdrop: true});
            $('#modal #confirmed-delete').data('id', $(this).data('id'));
            $(this).button('loading');
            $('#modal').modal('show');
        });
    });
}



$(document).ready(function() {
    load('status');
    load('history');
    load('config');
    load('files');
    $('.alert .close').click(function(){
        $('.alert').fadeOut();
    });
    $('#confirmed-delete').click(function(){
        $('#modal').modal('hide');
        $('#file-' + $(this).data('id') + ' .confirm-file-delete').button('loading');
        $.get('/delete/' + $(this).data('id'), function(data) {
            $('.confirm-file-delete').button('reset');
            console.log(data);
            if (data.status != 200) {
                $('.alert #error-msg').html(data.error);
                $('.alert').hide();
                $('.alert').removeClass('hidden');
                $('.alert').fadeIn();
            } else {
                $('#file-' + data.id).fadeOut();
            }
        })
    });
    $('#modal').on('hide', function(){
        $('.confirm-file-delete').button('reset');
    });
    $('#modal').on('show', function(){
        $('#modal').removeClass('hidden');
    });
});
