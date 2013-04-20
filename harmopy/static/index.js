var store = {
    status: {},
    history: {},
    config: {},
    files: {},
};

var templates = {};

load = function(id) {
    // Load the json into the template and append it to the elem
    $.get('/' + id, function(data){
        $('#' + id + ' .data').html('');
        $.each([].concat(data), function(i, elem) {
            store[id][elem.id] = elem;
            if (elem.id == 'DEFAULT')
                return;
            var html = templates[id](elem);
            $('#' + id + ' .loading').hide();
            $('#' + id + ' .data').append(html);
            $('#' + id + ' .showondata').removeClass('hidden');
        });
        if(id == 'files')
            on_file_load(data);
    });
};

on_file_load = function(data) {
    if(!data[0].editable) {
        $('#edit-defaults').addClass('hidden');
        return;
    }

    $('#edit-defaults').removeClass('hidden');
    $('.do-file-edit').click(function() {
        var data = store.files[$(this).data('id')];
        var html = templates.file_edit(data);
        $('#file-edit .data').html(html);
        $('#file-edit').hide();
        $('#file-edit').removeClass('hidden');
        $('#file-edit').fadeIn();
    });
    $('.confirm').click(function() {
        $(this).button('loading');
        $('#modal #confirmed').data('id', $(this).data('id'));
        $('#modal #confirmed').data('action', $(this).data('action'));
        $('#modal #modal-message').html($(this).data('confirm-message'));
        $('#modal').modal('show');
    });
};

Handlebars.registerHelper('file_config', function(title, name, file) {
    var placeholder = store.files['DEFAULT'][name];
    if(name == 'id')
        placeholder = '';
    return new Handlebars.SafeString(templates.file_config({
        'name': name,
        'title': title,
        'placeholder': placeholder,
        'value': (file && (file.id == 'DEFAULT' || file[name] != placeholder)) ? file[name] : '',
    }));
});

$(document).ready(function() {
    templates = {
        status: Handlebars.compile($('#status-template').html()),
        history: Handlebars.compile($('#history-template').html()),
        config: Handlebars.compile($('#config-template').html()),
        files: Handlebars.compile($('#files-template').html()),
        file_edit: Handlebars.compile($('#file_edit-template').html()),
        file_config: Handlebars.compile($('#file_config-template').html()),
    }
    load('status');
    load('history');
    load('config');
    load('files');
    $('.alert .close').click(function(){
        $('.alert').fadeOut();
    });
    $('#confirmed').click(function(){
        $('#modal').modal('hide');
        var action = $(this).data('action');
        $('#file-' + $(this).data('id') + ' .file-' + action).button('loading');
        $.get('/' + action + '/' + $(this).data('id'), function(data) {
            $('.confirm').button('reset');
            if (data.status != 200) {
                $('.alert #error-msg').html(data.error);
                $('.alert').hide();
                $('.alert').removeClass('hidden');
                $('.alert').fadeIn();
            } else {
                if(action == 'delete')
                    $('#file-' + data.id).fadeOut();
                else if(action == 'expand'){
                    $.each(data.files, function(i, file) {
                        $(templates.files(file).trim()).insertAfter('#file-' + data.id);
                    });
                    $('#file-'+data.id).fadeOut();
                }
            }
        })
    });
    $('#modal').on('hide', function(){
        $('.confirm').button('reset');
        $('.confirm').button('reset');
    });
    $('#modal').on('show', function(){
        $('#modal').removeClass('hidden');
    });
});
