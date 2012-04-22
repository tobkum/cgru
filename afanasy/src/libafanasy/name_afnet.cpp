#include "name_af.h"

#ifndef WINNT
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#define closesocket close
#endif

#include "address.h"
#include "environment.h"
#include "msg.h"
#include "msgstat.h"

#define AFOUTPUT
#undef AFOUTPUT
#include "../include/macrooutput.h"

af::MsgStat mgstat;

/// Read data from file descriptor. Return bytes than was written or -1 on any error and prints an error in \c stderr.
int readdata( int fd, char* data, int data_len, int buffer_maxlen)
{
    AFINFA("readdata: trying to recieve %d bytes.\n", data_len);
    int bytes = 0;
    while( bytes < data_len )
    {
#ifdef WINNT
        int r = recv( fd, data+bytes, buffer_maxlen-bytes, 0);
#else
        int r = read( fd, data+bytes, buffer_maxlen-bytes);
#endif
        if( r < 0)
        {
            AFERRPE("readdata: read");
            return -1;
        }
        AFINFA("readdata: read %d bytes.\n", r);
        if( r == 0) return bytes;
        bytes += r;
    }

    return bytes;
}

/// Write data to file descriptor. Return \c false on any arror and prints an error in \c stderr.
bool writedata( int fd, const char * data, int len)
{
    int written_bytes = 0;
    while( written_bytes < len)
    {
#ifdef WINNT
        int w = send( fd, data+written_bytes, len, 0);
#else
        int w = write( fd, data+written_bytes, len);
#endif
        if( w < 0)
        {
            AFERRPE("name_afnet.cpp writedata:");
            return false;
        }
        written_bytes += w;
    }
    return true;
}

// Return header offset
int processHeader( af::Msg * io_msg, int i_bytes, int i_desc)
{
//printf("\nReceived %d bytes:\n", i_bytes);
	char * buffer = io_msg->buffer();
	int offset = 0;
	bool founded = false;
	int min_after = 13;

	if( strncmp( buffer, "POST", 4) == 0 )
	{
		offset = 4;
		while( offset+min_after < i_bytes )
		{
			if( strncmp("[ * AFANASY * ]", buffer+offset, 15) == 0)
			{
				founded = true;
				break;
			}
			else
				while( offset+min_after < i_bytes )
					if( buffer[offset++] == '\n')
						break;
		}
	}

	if( founded || ( strncmp("[ * AFANASY * ]", buffer, 15) == 0 ))
	{
		offset += 15;
//writedata( 1, buffer+offset, i_bytes);
		int magic, sid, size;
		int num = sscanf( buffer + offset, "%d %d %d", &magic, &sid, &size);
//printf("\n sscanf=%d\n",num);
		if( num == 3 )
		{
			while( ++offset < i_bytes )
			{
				if( strncmp( buffer+offset, "JSON", 4) == 0)
				{
					offset += 3;
					while( ++offset < i_bytes )
					{
						if( buffer[offset] == '{' )
						{
							//printf("FOUNDED: %d %d %d Offset=%d:\n", magic, sid, size, offset);
							//write(1, buffer, offset);
							//write(1, buffer+offset, i_bytes - offset);
							//write(1,"\n",1);
							io_msg->setHeader( magic, sid, af::Msg::TJSON, size, offset, i_bytes);
							//return false;
							//io_msg->stdOutData();
							return offset;
						}
					}
				}
			}
			return -1;
		}
	}

	if( strncmp( buffer, "GET", 3) == 0 )
	{
		//writedata( 1, buffer, io_bytes);
		int get_start = 4;
		int get_finish = get_start; 
		char * data = NULL;
		int datalen;
		std::string datafile;
		while( buffer[++get_finish] != ' ');
		if( get_finish - get_start > 1 )
		{
			datafile = std::string( buffer + get_start, get_finish - get_start);
//printf("GET[%d,%d]=%s\n", get_start, get_finish, datafile.c_str());
			datafile = af::Environment::getAfRoot() + datafile;
			std::string error;
			data = af::fileRead( datafile, datalen, -1, &error);
		}
		else
		{
			datafile = af::Environment::getAfRoot() + "/" + "browser.html";
			data = af::fileRead( datafile, datalen);
		}

		if( data == NULL )
		{
			static const char httpError[] = "HTTP/1.0 404 Not Found\r\n\r\n";
			writedata( i_desc, httpError, strlen(httpError));
		}
		else
		{
			static const char httpHeader[] = "HTTP/1.0 200 OK\r\n\r\n";
			writedata( i_desc, httpHeader, strlen(httpHeader));
			writedata( i_desc, data, datalen);
		}
		return -1;
	}

	io_msg->readHeader( i_bytes);

	return af::Msg::SizeHeader;
}

af::Msg * msgsendtoaddress( const af::Msg * i_msg, const af::Address & i_address,
                            bool & io_ok, af::VerboseMode i_verbose)
{
    io_ok = true;

    if( i_address.isEmpty() )
    {
        AFERROR("af::msgsend: Address is empty.")
        io_ok = false;
        return NULL;
    }

    int socketfd;
    struct sockaddr_storage client_addr;

    if( false == i_address.setSocketAddress( &client_addr)) return NULL;

    if(( socketfd = socket( client_addr.ss_family, SOCK_STREAM, 0)) < 0 )
    {
        AFERRPE("af::msgsend: socket() call failed")
        io_ok = false;
        return NULL;
    }

    AFINFO("af::msgsend: tying to connect to client.")
/*
    // Use SIGALRM to unblock
#ifndef WINNT
    if( alarm(2) != 0 )
        AFERROR("af::msgsend: alarm was already set.\n");
#endif //WINNT
*/

    if( connect(socketfd, (struct sockaddr*)&client_addr, i_address.sizeofAddr()) != 0 )
    {
        if( i_verbose == af::VerboseOn )
        {
            AFERRPA("af::msgsend: connect failure for msgType '%s':\n%s: ",
                af::Msg::TNAMES[i_msg->type()], i_address.generateInfoString().c_str())
        }
        closesocket(socketfd);
/*
#ifndef WINNT
        alarm(0);
#endif //WINNT
*/
        io_ok = false;
        return NULL;
    }
/*
#ifndef WINNT
    alarm(0);
#endif //WINNT
*/
    //
    // set socket maximum time to wait for an output operation to complete
#ifndef WINNT
    timeval so_sndtimeo;
    so_sndtimeo.tv_sec = af::Environment::getServer_SO_SNDTIMEO_SEC();
    so_sndtimeo.tv_usec = 0;
    if( setsockopt( socketfd, SOL_SOCKET, SO_SNDTIMEO, &so_sndtimeo, sizeof(so_sndtimeo)) != 0)
    {
        AFERRPE("af::msgsend: set socket SO_SNDTIMEO option failed")
        i_address.stdOut(); printf("\n");
    }
    int nodelay = 1;
    if( setsockopt( socketfd, IPPROTO_TCP, TCP_NODELAY, &nodelay, sizeof(nodelay)) != 0)
    {
       AFERRPE("af::msgsend: set socket TCP_NODELAY option failed");
       i_address.stdOut(); printf("\n");
    }
#endif //WINNT
    //
    // send
    if( false == af::msgwrite( socketfd, i_msg))
    {
        AFERRAR("af::msgsend: can't send message to client: %s",
                i_address.generateInfoString().c_str())
        closesocket(socketfd);
        io_ok = false;
        return NULL;
    }

    if( false == i_msg->isReceiving())
    {
        closesocket(socketfd);
        return NULL;
    }

    //
    // read answer
    af::Msg * o_msg = new af::Msg();
    if( false == af::msgread( socketfd, o_msg))
    {
       AFERROR("MsgAf::request: reading message failed.\n");
       closesocket( socketfd);
       delete o_msg;
       io_ok = false;
       return NULL;
    }

    closesocket(socketfd);
    return o_msg;
}

void af::statwrite( af::Msg * msg)
{
   mgstat.writeStat( msg);
}
void af::statread( af::Msg * msg)
{
   mgstat.readStat( msg);
}

void af::statout( int columns, int sorting)
{
   mgstat.stdOut( columns, sorting);
}

const af::Address af::solveNetName( const std::string & i_name, int i_port, int i_type, VerboseMode i_verbose)
{
    if( i_verbose == af::VerboseOn )
    {
        printf("Solving '%s'", i_name.c_str());
        switch( i_type)
        {
            case AF_UNSPEC: break;
            case AF_INET:  printf(" and IPv4 forced"); break;
            case AF_INET6: printf(" and IPv6 forced"); break;
            default: printf(" (unknown protocol forced)");
        }
        printf("...\n");
    }

    struct addrinfo *res;
    struct addrinfo hints;
    memset( &hints, 0, sizeof(hints));
    hints.ai_flags = AI_ADDRCONFIG;
 //   hints.ai_family = AF_UNSPEC; // This is value is default
    hints.ai_socktype = SOCK_STREAM;
    char service_port[16];
    sprintf( service_port, "%u", i_port);
    int err = getaddrinfo( i_name.c_str(), service_port, &hints, &res);
    if( err != 0 )
    {
        AFERRAR("af::solveNetName:\n%s", gai_strerror(err))
        return af::Address();
    }

    for( struct addrinfo *r = res; r != NULL; r = r->ai_next)
    {
        // Skip address if type is forced
        if(( i_type != AF_UNSPEC ) && ( i_type != r->ai_family)) continue;

        if( i_verbose == af::VerboseOn )
        {
            switch( r->ai_family)
            {
                case AF_INET:
                {
                    struct sockaddr_in * sa = (struct sockaddr_in*)(r->ai_addr);
                    printf("IP = %s\n", inet_ntoa( sa->sin_addr));
                    break;
                }
                case AF_INET6:
                {
                    static const int buffer_len = 256;
                    char buffer[buffer_len];
                    struct sockaddr_in6 * sa = (struct sockaddr_in6*)(r->ai_addr);
                    const char * addr_str = inet_ntop( AF_INET6, &(sa->sin6_addr), buffer, buffer_len);
                    printf("IPv6 = %s\n", addr_str);
                    break;
                }
                default:
                    printf("Unknown address family type = %d\n", r->ai_family);
                    continue;
            }
        }

        af::Address addr((struct sockaddr_storage*)(r->ai_addr));

        if( i_verbose == af::VerboseOn )
        {
            printf("Address = ");
            addr.stdOut();
        }

        // Free memory allocated for addresses:
        freeaddrinfo( res);

        return addr;

    }

    // Free memory allocated for addresses:
    freeaddrinfo( res);

    return af::Address();
}

bool af::msgread( int desc, af::Msg* msg)
{
AFINFO("com::msgread:\n");

   char * buffer = msg->buffer();
//
// Read message header data
   int bytes = ::readdata( desc, buffer, af::Msg::SizeHeader, af::Msg::SizeBuffer );

   if( bytes < af::Msg::SizeHeader)
   {
      AFERRAR("com::msgread: can't read message header, bytes = %d (< Msg::SizeHeader).\n", bytes);
      msg->setInvalid();
      return false;
   }

	// Header offset is variable on not binary header (http)
	int header_offset = processHeader( msg, bytes, desc);
	if( header_offset < 1)
		return false;

	//
	// Read message data if any
	if( msg->type() >= af::Msg::TDATA)
	{
		buffer = msg->buffer(); // buffer may be changed to fit new size
		bytes -= header_offset;
		int readlen = msg->dataLen() - bytes;
		if( readlen > 0)
		{
//printf("Need to read more %d bytes of data:\n", readlen);
			bytes = ::readdata( desc, buffer + af::Msg::SizeHeader + bytes, readlen, readlen);
			if( bytes < readlen)
			{
				AFERRAR("af::msgread: read message data: ( bytes < readlen : %d < %d)", bytes, readlen)
				msg->setInvalid();
				return false;
			}
		}
	}
//msg->stdOutData();
	mgstat.put( msg->type(), msg->writeSize());

	return true;
}

bool af::msgwrite( int i_desc, const af::Msg * i_msg)
{
	int offset = 0;
	if( i_msg->type() == af::Msg::TJSON )
		offset = af::Msg::SizeHeader;

    if( false == ::writedata( i_desc, i_msg->buffer() + offset, i_msg->writeSize() - offset ))
    {
        AFERROR("com::msgsend: Error writing message.\n");
        return false;
    }

    mgstat.put( i_msg->type(), i_msg->writeSize());

    return true;
}

af::Msg * af::msgsend( Msg * i_msg, bool & io_ok, VerboseMode i_verbose )
{
    if( i_msg->isReceiving() && ( i_msg->addressesCount() > 0 ))
    {
        AFERROR("af::msgsend: Receiving message has several addresses.");
    }

    if( i_msg->addressIsEmpty() && ( i_msg->addressesCount() == 0 ))
    {
        AFERROR("af::msgsend: Message has no addresses to send to.");
        io_ok = false;
        i_msg->stdOut();
        return NULL;
    }

    if( false == i_msg->addressIsEmpty())
    {
        af::Msg * o_msg = ::msgsendtoaddress( i_msg, i_msg->getAddress(), io_ok, i_verbose);
        if( o_msg != NULL )
            return o_msg;
    }

    if( i_msg->addressesCount() < 1)
        return NULL;

    bool ok;
    const std::list<af::Address> * addresses = i_msg->getAddresses();
    std::list<af::Address>::const_iterator it = addresses->begin();
    std::list<af::Address>::const_iterator it_end = addresses->end();
    while( it != it_end)
    {
        ::msgsendtoaddress( i_msg, *it, ok, i_verbose);
        if( false == ok )
        {
            io_ok = false;
            // Store an address that message was failed to send to
            i_msg->setAddress( *it);
        }
        it++;
    }

    return NULL;
}