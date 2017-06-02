define(
  'commentStorage',
  function () {
    return {
      all: function () {
        return JSON.parse(sessionStorage.localComments || '[]');
      },

      addComment: function (newComment) {
        var comments = this.all()
        comments.push(newComment);
        return this.saveBulk(comments);
      },

      addReply: function (cid, replyData) {
        var self = this;
        var comments = this.all();

        for (var i = 0; i < comments.length; i++) {
          if (comments[i].cid === cid) {
            comments[i].replies.push(replyData)
            return this.saveBulk(comments);
          }
        }

        return false;
      },

      delete: function (cid) {
        var comments = this.all();

        for (var i = 0; i < comments.length; i++) {
          if (comments[i].cid === cid) {
            var removed = comments.splice(i, 1);
            return this.saveBulk(comments);
          }
        }
      },

      saveBulk: function (comments) {
        try {
          sessionStorage.localComments = JSON.stringify(comments);
          return true;
        } catch (err) {
          console.log('Error while saving comments into storage');
          return false;
        }
      },

      clear: function () {
        sessionStorage.removeItem('localComments');
      },
    }
  }
);


define([
    'aloha',
    'aloha/selection',
    'PubSub',
    'booktype',
    'react',
    'tools/autosize.min',
    'jsx!react_components/modal',
    'commentStorage'
  ],
  function (Aloha, Selection, PubSub, booktype, React, autosize, Modal, commentStorage) {

    var ReplyForm = React.createClass({
      getInitialState: function () {
        return { enableSubmit: false, replyValue: ''}
      },

      componentDidMount: function () {
        autosize(this.refs.replyArea);
      },

      showActions: function () {
        jQuery(this.refs.actions).removeClass('hide');
      },

      hideActions: function () {
        jQuery(this.refs.actions).addClass('hide');
      },

      resetActions: function () {
        this.hideActions();

        // Dispatch a 'autosize:update' event to trigger a resize:
        var evt = document.createEvent('Event');
        evt.initEvent('autosize:update', true, false);
        this.refs.replyArea.dispatchEvent(evt);
      },

      handleReplyChange: function (event) {
        var newValue = event.target.value;
        this.setState({
          replyValue: newValue,
          enableSubmit: (newValue.length > 0)
        })
      },

      onReply: function (event) {
        var self = this;

        var successAction = function () {
          // clean state and hide actions
          setTimeout(function () {
            self.setState({ replyValue: ''});
            self.resetActions();
          }, 200);

          // now time to reload comments
          PubSub.pub('booktype-pull-latest-comments');
        };

        if (this.props.local) {
          var replyData = {
            'parent_id': this.props.cid,
            'cid': booktype.utils.uuid4(),
            'date': moment().unix(), // unix timestamp
            'content': this.state.replyValue,
            'chapter_id': booktype.editor.edit.getChapterID(),
            'author': {
              name: booktype.fullname,
              username: booktype.username,
              avatar: booktype.utils.getAvatar(booktype.username, 35)
            }
          };
          commentStorage.addReply(this.props.cid, replyData);
          successAction();
        } else {
          booktype.sendToCurrentBook({
            'command': 'reply_comment',
            'content': self.state.replyValue,
            'comment_id': self.props.cid,
            'chapter_id': booktype.editor.edit.getChapterID()
          }, function (data) {
            if (data.result === false) {
              var noPermissions = booktype._('no_permissions', 'You do not have permissions for this.')
              booktype.utils.alert(noPermissions);
              return;
            }
            successAction();
          });
        }
      },

      render: function () {
        var replyClass = "form-control reply-input " + (this.props.fixedArea ? "full" : "");
        var actionsClass = "reply-actions hide " + (this.props.fixedArea ? "full" : "");

        var canReply = this.props.permissions.add_comment;
        var replyFormClass = "reply-form" + (canReply ? "" : " hide");

        return (
          <form role="form" className={replyFormClass}>
            <div className="form-group">
              <textarea ref="replyArea" rows="1"
                className="form-control" placeholder="Reply..."
                value={this.state.replyValue} onChange={this.handleReplyChange}
                className={replyClass} onFocus={this.showActions}
              />
            </div>
            <div ref="actions" className={actionsClass}>
              <button
                className="btn btn-primary btn-sm" type="button"
                onClick={this.onReply}
                disabled={!this.state.enableSubmit}>
                  {booktype._('reply', 'Reply')}
              </button>
              <button type="button" onClick={this.hideActions}
                className="btn btn-default btn-sm">
                {booktype._('cancel', 'Cancel')}
              </button>
            </div>
          </form>
        );
      }
    });

    var CommentEntry = React.createClass({
      propTypes: {
        commentType: React.PropTypes.string.isRequired
      },

      render: function () {
        var commentTypeClass = ("media " + this.props.commentType);

        return (
          <div className={commentTypeClass}>
            <a className="pull-left" href="#">
             <img src={this.props.author.avatar} className="user-avatar" />
            </a>
            <div className="media-body">
              <b>{this.props.author.name}</b><br />
              <span className="comment-date" title={moment(this.props.date, 'X').format('MMM Do, YYYY HH:mm:ss')}>{moment(this.props.date, 'X').fromNow()}</span>
            </div>
            <div className="comment-content">
              <p>{this.props.content}</p>
            </div>
          </div>
        );
      }
    });

    var CommentBox = React.createClass({

      getInitialState: function () {
        return {
          replies: this.props.replies || [],
        };
      },

      componentWillReceiveProps: function(nextProps) {
        this.setState({ replies: nextProps.replies });
      },

      componentWillMount: function () {
        PubSub.unsub(this.bubbleSelectSubId);
      },

      componentDidMount: function () {
        var self = this;
        var commentBox = jQuery(this.refs.commentBox);
        var commentTab = jQuery('#commentsTab');

        this.bubbleSelectSubId = PubSub.sub('booktype-comment-bubble-selected', function (data) {
          var isCurrentBox = (data.cid === self.props.cid);
          commentBox.toggleClass('selected', isCurrentBox);

          if (isCurrentBox) {
            if (commentBox.offset()) {
              var top = commentBox.offset().top - commentTab.parent('.scrollable').offset().top;
              commentTab.parent('.scrollable').scrollTop(top);
            }
          }
        });
      },

      renderReplies: function () {
        return this.state.replies.map(function (reply) {
          return (
            <CommentEntry key={reply.cid} {...reply} commentType="reply-comment" />
          );
        });
      },

      handleAction: function (action) {
        var self = this;
        booktype.utils.confirm({
          message: booktype._(action + '_comment', 'Do you want to ' + action + ' this comment?')},
          function (res) {
            if (res) {
              var successAction = function () {
                jQuery('#comment-id-' + self.props.cid).remove();
                booktype.editor.edit.disableSave(false);

                // update the comments list
                PubSub.pub('booktype-pull-latest-comments');

                var saveChapter = booktype._('forget_save_chapter', 'Do not forget to save the chapter to preserve the changes!')
                booktype.utils.alert(saveChapter);
              };

              if (self.props.local) {
                commentStorage.delete(self.props.cid);
                successAction();
              } else {
                booktype.sendToCurrentBook(
                  {
                    'command': action + '_comment',
                    'chapter_id': booktype.editor.edit.getChapterID(),
                    'comment_id': self.props.cid
                  },
                  function (data) {
                    if (data.result === false) {
                      var noPermissions = booktype._('no_permissions', 'You do not have permissions for this.')
                      booktype.utils.alert(noPermissions);
                      return;
                    }
                    successAction();
                  }
                );
              }
            }
          }
        );
      },

      replyAction: function () {
        var domObj = ReactDOM.findDOMNode(this.refs.replyForm);
        jQuery(domObj).find('textarea').focus();
      },

      handleClick: function (event) {
        // unselect other boxes and bubbles just in case
        jQuery('.comment-box.selected').removeClass('selected');
        jQuery('a.comment-link').removeClass('comment-selected');

        // mark current box try to reveal reference bubble in editor
        jQuery(this.refs.commentBox).addClass('selected');
        jQuery('a[id="comment-id-' + this.props.cid + '"]').addClass('comment-selected');
      },

      renderMenuOption: function (key, label, clickHandler) {
        var permissions = this.props.permissions;
        var permKey = key + '_comment'
        if (permissions[permKey])
          return <li><a href="javascript:;" onClick={clickHandler}>{label}</a></li>;
        return null;
      },

      render: function () {
        return (
          <div ref="commentBox" className="comment-box" onClick={this.handleClick}>
            <div className="comment-reference pull-left">
              {this.props.text}
            </div>

            <div className="btn-group pull-right">
              <button type="button" className="btn btn-default btn-xs dropdown-toggle" data-toggle="dropdown">
                {booktype._('actions', 'Actions')} <span className="caret"></span>
              </button>
              <ul className="dropdown-menu" role="menu">
                {this.renderMenuOption('resolve', booktype._('resolve'), this.handleAction.bind(this, 'resolve'))}
                {this.renderMenuOption('delete', booktype._('delete'), this.handleAction.bind(this, 'delete'))}
                {this.renderMenuOption('add', booktype._('reply'), this.replyAction)}
              </ul>
            </div>

            <CommentEntry {...this.props} commentType="initial-comment" />
            {this.renderReplies()}

            <ReplyForm {...this.props} ref="replyForm" fixedArea={this.state.replies.length === 0} />
          </div>
        );
      }
    });

    var CommentList = React.createClass({

      getInitialState: function () {
        return {
          comments: this.props.comments || [],
          permissions: this.props.permissions || {}
        };
      },

      componentWillUnmount: function () {
        // unbind events
        PubSub.unsub(this.latestCommentsSubId);

        // let's wait a bit until we unbind this one
        setTimeout(function () {
          jQuery(document).off('booktype-document-saved');
        }, 1000);
      },

      componentDidMount: function () {
        // remove local comments to avoid old unreferenced comments
        commentStorage.clear()

        var self = this;
        this.latestCommentsSubId = PubSub.sub('booktype-pull-latest-comments', function (e) {
          booktype.sendToCurrentBook({
              'command': 'get_comments',
              'resolved': false,
              'chapter_id': booktype.editor.edit.getChapterID()
            },
            function (data) {
              // pull local comments also and join with the one coming from server
              var localComments = commentStorage.all();
              var comments = _.union(data.comments, localComments);
              self.setState({comments: comments, permissions: data.permissions});
            }
          );
        });

        // clear comment storage when leaving window
        window.onbeforeunload = commentStorage.clear;

        // listen to chapter save so we save sessionStorage comments and then clean storage
        jQuery(document).on('booktype-document-saved', function (event, doc) {
          booktype.sendToCurrentBook({
              'command': 'save_bulk_comments',
              'chapter_id': booktype.editor.edit.getChapterID(),
              'local_comments': commentStorage.all()
            },
            function (data) {
              if (data.result === false) {
                var noPermissions = booktype._('no_permissions', 'You do not have permissions for this.')
                booktype.utils.alert(noPermissions);
                return;
              }

              // clean comments storage
              commentStorage.clear();

              // pull latest comments from server
              PubSub.pub('booktype-pull-latest-comments');
            }
          );
        });
      },

      noCommentsHandler: function () {
        var insertCommentBtn = jQuery('.btn-toolbar .comment-insert')[0];
        booktype.utils.triggerClick(insertCommentBtn);
      },

      render: function () {
        var self = this;
        var comments = this.state.comments || [];
        var permissions = this.state.permissions || {};
        var commentItems = comments.map(function (comment) {
          return <CommentBox key={comment.cid} permissions={permissions} {...comment} />;
        });

        var addCommentMsg = function () {
          return (
            <div>
              {booktype._('insert_comment_text')}
              <br /><br />
              <button onClick={self.noCommentsHandler} className="btn btn-sm btn-primary no-comments-yet-btn disabled">
                {booktype._('insert_comment_btn')}
              </button>
              <br /><br />
            </div>
          );
        };

        return (
          <div>
            {addCommentMsg()}
            {commentItems}
          </div>
        );
      }
    });

    var InsertCommentModal = React.createClass({
      getInitialState: function () {
        return { commentedText: '' };
      },

      componentDidMount: function () {
        autosize(this.refs.textarea);
      },

      handleCommentChange: function (event) {
        var newValue = event.target.value;

        this.setState({comment: newValue});
        this.refs.modal.enableConfirm(jQuery.trim(newValue).length > 0);
      },

      show: function (range, editable, handleBubbleClick) {
        this.range = range;
        this.editable = editable;
        this.handleBubbleClick = handleBubbleClick;

        this.setState({commentedText: range.getText()});
        this.refs.modal.show();
      },

      onShown: function () {
        this.refs.textarea.focus();
        this.setState({comment: ''});
      },

      onConfirm: function () {
        var self = this;
        var range = this.range;
        var editable = this.editable;

        // save comments in localStorage until the user clicks save chapter
        var commentData = {
          'local': true,
          'cid': booktype.utils.uuid4(),
          'content': this.state.comment,
          'text': this.state.commentedText,
          'date': moment().unix(), // unix timestamp
          'chapter_id': booktype.editor.edit.getChapterID(),
          'author': {
            'name': booktype.fullname,
            'username': booktype.username,
            'avatar': booktype.utils.getAvatar(booktype.username, 35)
          },
          'replies': []
        };
        commentStorage.addComment(commentData);

        var commentBubble = jQuery([
          '<a href="javascript:;" id="comment-id-', commentData.cid,
          '" class="comment-link"><i class="fa fa-comment"></i></a>'].join('')
        );
        commentBubble.on('click', self.handleBubbleClick);

        var dom = GENTICS.Utils.Dom;
        dom.insertIntoDOM(commentBubble, range, editable.obj, true);
        range.select();

        booktype.editor.edit.disableSave(false);
        self.refs.modal.hide();

        var saveChapter = booktype._('forget_save_chapter', 'Do not forget to save the chapter to preserve the changes!')
        booktype.utils.alert(saveChapter);

        PubSub.pub('booktype-pull-latest-comments');
      },

      render: function () {
        var props = {
          title: booktype._('new_comment', 'New comment'),
          cancelText: booktype._('cancel', 'Cancel'),
          submitText: booktype._('save', 'Save'),
          onConfirm: this.onConfirm,
          cssClass: 'comment-modal',
        };

        return (
          <Modal ref="modal"
            id='newCommentModal' onShown={this.onShown} {...props}>
            <div className="comment-reference">{this.state.commentedText}</div>
            <textarea
              ref="textarea" className="form-control"
              placeholder="Write your comment here"
              value={this.state.comment} onChange={this.handleCommentChange}></textarea>
          </Modal>
        );
      }
    });

    return {
      InsertCommentModal: InsertCommentModal,
      CommentList: CommentList
    };
  }
);
