horizon.policies = {
  /* Update input attributes for column name autocompletion. */
  updateColumnAcInput: function($input) {
    $input.attr({
      'placeholder': $input.attr('data-column-example'),
      'pattern': $input.attr('data-pattern'),
      'title': $input.attr('data-pattern-error')
    });
    /* form-control-feedback only hidden, so it still has autocompletion. */
    $input.closest('td').find('.form-control-feedback')
      .removeClass('hidden');
  },

  /* Get column names from conditions mappings. */
  getMappedColumns: function() {
    var mappings = [];
    $('#mappings_table').find('.policy-column-name').each(function() {
      var $td = $(this);
      var column = $td.text();
      if (column) {
        mappings.push(column);
      }
    });
    return mappings;
  },

  /* Check if any columns need to be removed from conditions mappings. */
  scrubMappedColumns: function(columns) {
    mappings = horizon.policies.getMappedColumns();
    if (!columns) {
      columns = [];
      var $inputs = $('#policy_columns_table').find('.policy-column-input');
      $inputs.each(function() {
        var $input = $(this);
        var name = $input.val();
        if (name) {
          columns.push(name);
        }
      });
    }

    for (var i = 0; i < mappings.length; i++) {
      var name = mappings[i];
      if ($.inArray(name, columns) == -1) {
        $('#mappings_table').find('.policy-column-name:contains(' +
                                    name + ')').closest('tr').remove();
      }
    }
    /* Put label back if there's only one row left without it. */
    var $rows = $('#mappings_table').find('.mapping-row');
    if ($rows.length == 1 && !$rows.find('.label-cell').text()) {
      var label = $('#mapping_0').find('.label-cell').html();
      $rows.find('.label-cell').html(label);
    }
  },
}

horizon.addInitFunction(horizon.policies.init = function() {
  /* Add another policy table column name. */
  $(document).on('click', '#add_policy_column_button', function(evt) {
    evt.preventDefault();
    var $button = $(this);
    var $tr = $('#policy_column_0').clone();

    var count = $button.attr('data-count');
    var cid = parseInt(count);
    $button.attr('data-count', cid + 1);

    /* Change ids and reset inputs. */
    $tr.attr('id', 'policy_column_' + cid);
    $tr.find('input[name]').val('').each(function() {
      this.name = this.name.replace(/^(.+_)\d+$/, '$1' + cid);
    });
    $tr.find('.remove-policy-column-button').removeClass('hidden');
    /* Add row before the one reserved for errors. */
    $('#policy_columns_table').find('tr:last').before($tr);
  });

  /* Remove policy table column name input. */
  $(document).on('click',
                 '#policy_columns_table a.remove-policy-column-button',
                 function(evt) {
    evt.preventDefault();
    var $a = $(this);
    var $tr = $a.closest('tr');
    $tr.remove();
    horizon.policies.scrubMappedColumns();
  });

  /* Add policy table columns to conditions and combine into single param. */
  $(document).on('change',
                 '#policy_columns_table input.policy-column-input',
                 function() {
    var mappings = horizon.policies.getMappedColumns();
    var columns = [];

    var $inputs = $('#policy_columns_table').find('.policy-column-input');
    $inputs.each(function() {
      var $input = $(this);
      var name = $input.val();
      /* Does not make sense to have multiple of the same column. */
      if (name && $.inArray(name, columns) == -1) {
        columns.push(name);

        if ($.inArray(name, mappings) == -1) {
          /* Add mapping inputs for new policy column. */
          var $tr = $('#mapping_0').clone();
          var count = $('#mappings_table').attr('data-count');
          var cid = parseInt(count);
          $('#mappings_table').attr('data-count', cid + 1);

          /* Change ids. */
          $tr.attr('id', 'mapping_' + cid).toggleClass('hidden mapping-row');
          $tr.find('.policy-column-name').text(name);
          $tr.find('input[id]').each(function() {
            this.id = this.id.replace(/^(.+_)\d+$/, '$1' + cid);
            this.name = this.id;
          });
          /* Remove label if there's already a row with it. */
          if ($('#mappings_table').find('.mapping-row').length) {
            $tr.find('.label-cell').empty();
          }
          $('#mappings_table').find('tr:last').before($tr);

          /* Add autocompletion. */
          $('#mapping_column_' + cid).autocomplete({
            minLength: 0,
            source: JSON.parse($('#ds_columns').text())
          });
          $('#mapping_' + cid).find('.ac div.form-control-feedback')
              .click(function() {
            /* Focus on list now so that clicking outside of it closes it. */
            $('#mapping_column_' + cid).autocomplete('search', '').focus();
          });
        }
      }
    });

    /* Workflow expects one policy_columns value. */
    $('#policy_columns').val(columns.join(', '));
    horizon.policies.scrubMappedColumns(columns);
  });

  /* Add another join. */
  $(document).on('click', '#add_join_button', function(evt) {
    evt.preventDefault();
    var $button = $(this);
    var $tr = $('#join_0').clone();

    var count = $button.attr('data-count');
    var cid = parseInt(count);
    $button.attr('data-count', cid + 1);

    /* Change ids and reset inputs. */
    $tr.attr('id', 'join_' + cid);
    $tr.find('input[id], select[id]').val('').each(function() {
      this.id = this.id.replace(/^(.+_)\d+$/, '$1' + cid);
      this.name = this.id;
    });
    $tr.find('select').val($tr.find('option:first').val());
    $tr.find('.remove-join-button').removeClass('hidden');
    $('#joins_table').append($tr);

    /* Add autocompletion. */
    $('#join_left_' + cid + ', #join_right_' + cid).autocomplete({
      minLength: 0,
      source: JSON.parse($('#ds_columns').text())
    });
    horizon.policies.updateColumnAcInput($('#join_right_' + cid));
    $('#join_' + cid).find('.ac div.form-control-feedback').click(function() {
      var $div = $(this);
      /* Focus on list now so that clicking outside of it closes it. */
      $div.siblings('.ac-columns').autocomplete('search', '').focus();
    });
  });

  /* Remove join input. */
  $(document).on('click', '#joins_table a.remove-join-button',
                 function(evt) {
    evt.preventDefault();
    var $a = $(this);
    var $tr = $a.closest('tr');
    $tr.remove();
  });

  /* Update input attributes based on type selected. */
  $(document).on('change', '#joins_table select.join-op', function() {
    var $select = $(this);
    var $input = $select.closest('tr').find('.join-right').val('');

    if (!$select.val()) {
      $input.autocomplete({
        minLength: 0,
        source: JSON.parse($('#ds_columns').text())
      });
      horizon.policies.updateColumnAcInput($input);
    } else {
      $input.closest('td').find('.form-control-feedback').addClass('hidden');
      $input.autocomplete('destroy');
      $input.attr('placeholder', $input.attr('data-static-example'));
      $input.removeAttr('pattern').removeAttr('title');
    }
  });

  /* Add another negation. */
  $(document).on('click', '#add_negation_button', function(evt) {
    evt.preventDefault();
    var $button = $(this);
    var $tr = $('#negation_0').clone();

    var count = $button.attr('data-count');
    var cid = parseInt(count);
    $button.attr('data-count', cid + 1);

    /* Change ids and reset inputs. */
    $tr.attr('id', 'negation_' + cid);
    $tr.find('input[id], select[id]').val('').each(function() {
      this.id = this.id.replace(/^(.+_)\d+$/, '$1' + cid);
      this.name = this.id;
    });
    $tr.find('select').val($tr.find('option:first').val());
    $tr.find('.remove-negation-button').removeClass('hidden');
    $('#negations_table').append($tr);

    /* Add autocompletion. */
    $('#negation_value_' + cid + ', #negation_column_' + cid).autocomplete({
      minLength: 0,
      source: JSON.parse($('#ds_columns').text())
    });
    $('#negation_' + cid).find('.ac div.form-control-feedback')
        .click(function() {
      var $div = $(this);
      /* Focus on list now so that clicking outside of it closes it. */
      $div.siblings('.ac-columns').autocomplete('search', '').focus();
    });
  });

  /* Remove negation input. */
  $(document).on('click', '#negations_table a.remove-negation-button',
                 function(evt) {
    evt.preventDefault();
    var $a = $(this);
    var $tr = $a.closest('tr');
    $tr.remove();
  });

  /* Add another alias. */
  $(document).on('click', '#add_alias_button', function(evt) {
    evt.preventDefault();
    var $button = $(this);
    var $tr = $('#alias_0').clone();

    var count = $button.attr('data-count');
    var cid = parseInt(count);
    $button.attr('data-count', cid + 1);

    /* Change ids and reset inputs. */
    $tr.attr('id', 'alias_' + cid);
    $tr.find('td:first').empty();
    $tr.find('input[id]').val('').each(function() {
      this.id = this.id.replace(/^(.+_)\d+$/, '$1' + cid);
      this.name = this.id;
    });
    $tr.find('.remove-alias-button').removeClass('hidden');
    $('#aliases_table').append($tr);

    /* Add autocompletion. */
    $('#alias_column_' + cid).autocomplete({
      minLength: 0,
      source: JSON.parse($('#ds_tables').text())
    });
    $('#alias_' + cid).find('.ac div.form-control-feedback')
        .click(function() {
      var $div = $(this);
      /* Focus on list now so that clicking outside of it closes it. */
      $div.siblings('.ac-tables').autocomplete('search', '').focus();
    });
  });

  /* Remove alias input. */
  $(document).on('click', '#aliases_table a.remove-alias-button',
                 function(evt) {
    evt.preventDefault();
    var $a = $(this);
    var $tr = $a.closest('tr');
    $tr.remove();
  });
});
