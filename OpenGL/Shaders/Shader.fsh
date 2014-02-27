//
//  Shader.fsh
//  OpenGL
//
//  Created by waltonmis on 2/27/14.
//  Copyright (c) 2014 waltonmis. All rights reserved.
//

varying lowp vec4 colorVarying;

void main()
{
    gl_FragColor = colorVarying;
}
