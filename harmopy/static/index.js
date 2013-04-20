var store = {
    status: [],
    history: [],
    config: [],
    files: []
};

var templates = {};

load = function(id) {
    // Load the json into the template and append it to the elem
    $.get('/' + id, function(data){
        $.each([].concat(data), function(i, elem) {
            store[id][elem.id] = elem;
            var html = templates[id](elem);
            $('#' + id + ' .loading').hide();
            $('#' + id + ' .data').append(html);
            $('#' + id + ' .showondata').removeClass('hidden');
        });
        $('.confirm-file-delete').click(function() {
            $('#modal #confirmed-delete').data('id', $(this).data('id'));
            $(this).button('loading');
            $('#modal').modal('show');
        });
        $('.do-file-edit').click(function() {
            var data = store.files[$(this).data('id')];
            var html = templates.file_edit(data);
            $('#file-edit .data').html(html);
            $('#file-edit').hide();
            $('#file-edit').removeClass('hidden');
            $('#file-edit').fadeIn();
        });
    });
}


$(document).ready(function() {
    templates = {
        status: Handlebars.compile($('#status-template').html()),
        history: Handlebars.compile($('#history-template').html()),
        config: Handlebars.compile($('#config-template').html()),
        files: Handlebars.compile($('#files-template').html()),
        file_edit: Handlebars.compile($('#file_edit-template').html())
    }
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
        $('#modal').modal({backdrop: true});
        $('#modal').removeClass('hidden');
    });
});
