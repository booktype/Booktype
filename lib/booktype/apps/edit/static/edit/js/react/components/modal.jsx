define([
    "require",
    "react"
  ],
  function (require, React) {
    var Modal = React.createClass({
      getInitialState: function () {
        return {confirmDisabled: true}
      },

      componentWillMount: function () {
        if (this.props.onShown)
          jQuery(document).on('shown.bs.modal', '#' + this.props.id, this.props.onShown);

        if (this.props.onHide)
          jQuery(document).on('hide.bs.modal', '#' + this.props.id, this.props.onHide);
      },

      componentWillUnmount: function () {
        // make sure to unbind just in case
        jQuery(document).off('shown.bs.modal');
      },

      show: function() {
        jQuery('#' + this.props.id).modal();
      },

      hide: function() {
        jQuery('#' + this.props.id).modal('hide');
      },

      confirm: function () {
        if (typeof this.props.onConfirm === 'function') this.props.onConfirm();
      },

      enableConfirm: function (value) {
        this.setState({confirmDisabled: !value});
      },

      render: function () {
        var cssClasses = 'modal ' + (this.props.cssClass || "");

        return (
          <div className={cssClasses} id={this.props.id} tabIndex="-1" role="dialog">
            <div className="modal-dialog">
              <div className="modal-content">
                <div className="modal-header">
                  <button type="button" className="close" data-dismiss="modal" aria-hidden="true">×</button>
                  <h3>{this.props.title}</h3>
                </div>
                <div className="modal-body">
                  {this.props.children}
                </div>
                <div className="modal-footer">
                  <button className="btn btn-default" data-dismiss="modal" aria-hidden="true">{this.props.cancelText}</button>
                  <button className="btn btn-primary confirm" onClick={this.confirm} disabled={this.state.confirmDisabled}>{this.props.submitText}</button>
                </div>
              </div>
            </div>
          </div>
        )
      }
    });

    return Modal;
  }
);
