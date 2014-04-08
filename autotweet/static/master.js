$(function() {
    $(window).on('submit', function(event){
        var target = $(event.target);

        if (target.hasClass('query')) {
            query(target);
        } else if (target.hasClass('teach')) {
            teach(target);
        }
        event.preventDefault();
    });

    function query(target) {
        var payload = target.serialize();
        var input = target.find('[name=query]');
        var query = input.val();
        var p = $('<p>');
        var span = $('<span>');
        var messages = $('#messages');

        span.text(query);
        span.addClass('msg');
        p.addClass('message');
        p.addClass('me');
        p.append(span)
        messages.append(p);

        input.val(null);

        $.post(target.attr('action'), payload, function(data) {
            if (data == '') {
                data = 'I cannot answer. please teach me.';
            }
            var p = $('<p>');
            var span = $('<span>');
            span.text(data);
            span.addClass('msg');
            p.addClass('message');
            p.addClass('other');
            p.append(span);
            messages.append(p);
            messages.scrollTop(messages[0].scrollHeight);
        });

        messages.scrollTop(messages[0].scrollHeight);
    }

    function teach(target) {
        var payload = target.serialize();

        $.post(target.attr('action'), payload, function() {
            target[0].reset();
        });
    }

    $('input[type=text]').focus();
});
