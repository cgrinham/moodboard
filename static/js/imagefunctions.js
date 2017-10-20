jQuery(document).ready(function() {
jQuery(function( $ ) {

    $('.delete').on('click', function() {

        absimage = $(this).closest('.userimage-container').data("absimage");
        //alert(absimage);

        original = $(this).parents('.userimage-container').children('a').children('img').attr("src");

        current_element = $(this).parents('.userimage-container').children('a').children('img');

        nothing = "nothing";

        jQuery.ajax({
            type: "POST",
            data: {action : "delete", prop1 : absimage, prop2 : nothing},
            success: function() {
                current_element.css("display", "none");
            }
        });
        return false;
    });

    $('#favourite').on('click', function() {
        user = $(this).data("user");

        jQuery.ajax({
            type: "POST",
            data: {action : "favourite", prop1: user, prop2 : "none"},
            success: function() {
                $("#favourite").text("favourited");
            }
        });
        return false;
    });

    $('.remove-favourite').on('click', function() {
        user = $(this).data("user");
        jQuery.ajax({
            type: "POST",
            data: {action : "unfavourite", prop1: user, prop2 : "none"},
            success: function(){},
            error: function(jqXHR, textStatus, errorThrown){}
        });

        $(this).parents(".usertile").css("display", "none");
        //$(this).parents(".user-tile").hide()
        //return false;
    });

    $('.move').on('change', function() {
        //alert($(this).find(":selected").val());
        folder = $(this).find(":selected").val();
        absimage = $(this).parents('.userimage-container').children('a').children('img').attr("src");
        //alert($(this).parents('.userimage-container').children('a').children('img').attr("src"))
        
        current_element = $(this).parents('.userimage-container');

        jQuery.ajax({
            type: "POST",
            data: {action : "move", prop1 : absimage, prop2 : folder},
            success: function() {
                current_element.remove();
            }
        });
        return false;
    });

    $('.rotate_cw, .rotate_ccw').on('click', function() {
        absimage = $(this).closest('.userimage-container').data("absimage");
        //alert(absimage);

        original = $(this).parents('.userimage-container').children('a').children('img').attr("src");
        //alert(original);

        current_element = $(this).parents('.userimage-container').children('a').children('img');

        direction = $(this).attr('class');
        jQuery.ajax({
            type: "POST",
            data: {action : "rotate", prop1 : absimage, prop2 : direction},
            success: function() {
                current_element.attr("src", original + "?" + new Date().getTime());
            }
        });
        return false;
    });


    
});

});

/*
$("id-" + image).attr("src", "../" + absimage + "?" + d.getTime());

jQuery(document).ready(function() {
jQuery(".button").click(function() {
        var input_string = $$("input#textfield").val();
        jQuery.ajax({
                type: "POST",
                data: {textfield : input_string},
                success: function(data) {
                jQuery('#foo').html(data).hide().fadeIn(1500);
                },
                });
        return false;
        });
});*/