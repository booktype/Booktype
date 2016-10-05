define([
  'jquery',
  'booktype/blockquote-manager',
  'jsx!react_components/modal'
], function (jQuery, BlockquoteManager, Modal) {
  var InsertBlockquoteModal = React.createClass({
    getInitialState: function () {
      return {
        quotedText: '',
        author: ''
      };
    },

    show: function (quotedText) {
      this.setState({
        quotedText: quotedText,
        author: ''
      });
      this.refs.modal.show();
    },

    onShown: function () {
      this.refs.quoteAuthor.focus();
      this.refs.modal.enableConfirm(true);
      jQuery(this.refs.blockquoteContent).attr('id', 'contenteditor');
    },

    onHide: function () {
      jQuery(this.refs.blockquoteContent).removeAttr('id');
    },

    onConfirm: function () {
      this.refs.modal.hide();
      BlockquoteManager.create(this.state.quotedText, this.state.author);
    },

    handleAuthorChange: function(event) {
      this.setState({author: event.target.value});
    },

    render: function () {
      var props = {
        title: booktype._('new_quote', 'New Quote'),
        cancelText: booktype._('cancel', 'Cancel'),
        submitText: booktype._('insert', 'Insert'),
        onConfirm: this.onConfirm,
        cssClass: 'comment-modal',
      };
      var author = this.state.author;
      var authorLabel = booktype._('quote_author_label');
      var authorPlaceholder = booktype._('quote_author_placeholder');

      return (
        <Modal ref="modal"
          id='insertBlockquoteModal' onShown={this.onShown} onHide={this.onHide} {...props}>
          <div ref="blockquoteContent">
            <blockquote>
              <p dangerouslySetInnerHTML={{__html: this.state.quotedText}}></p>
              <p className="bk-cite">{author}</p>
            </blockquote>
          </div>
          <label for="quote-author">{authorLabel}</label>
          <input
            value={author}
            ref="quoteAuthor"
            name="quote-author"
            className="form-control"
            placeholder={authorPlaceholder}
            onChange={this.handleAuthorChange}
          />
        </Modal>
      );
    }
  });

  // time to exports modules :P
  return {
    InsertBlockquoteModal: InsertBlockquoteModal
  }
});
