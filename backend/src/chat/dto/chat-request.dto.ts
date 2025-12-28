
import { IsString, IsOptional } from 'class-validator';

export class ChatRequestDto {
    @IsString()
    user_id: string;

    @IsString()
    message: string;

    @IsString()
    @IsOptional()
    session_id?: string;
}
